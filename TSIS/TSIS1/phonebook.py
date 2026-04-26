# phonebook.py
import csv
import json
import os
import sys
from datetime import datetime
from connect import get_connection

class PhoneBookExtended:
    """
    ПРОДВИНУТАЯ ТЕЛЕФОННАЯ КНИГА
    
    ЛОГИКА РАБОТЫ:
    Класс-обертка над PostgreSQL БД. При создании объекта - устанавливается соединение,
    при закрытии - разрывается. Все операции выполняются в транзакциях для сохранения целостности.
    
    ПРОДВИНУТЫЕ ФУНКЦИИ:
    1. Умный импорт CSV (UPSERT + дедупликация)
    2. JSON импорт с интерактивным разрешением конфликтов
    3. Пагинация через server-side функцию БД
    4. Динамическая сортировка с обработкой NULL
    5. Использование хранимых процедур
    6. Полнотекстовый поиск через функцию БД
    """
    
    def __init__(self):
        # ПРИНЦИП: соединение создается один раз и переиспользуется
        self.conn = get_connection()
        self.conn.autocommit = False   # РУЧНОЕ УПРАВЛЕНИЕ: каждый коммит явный

    def close(self):
        """ОБЯЗАТЕЛЬНО: закрываем соединение даже при ошибках (finally блок)"""
        self.conn.close()

    # ========== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ (DRY принцип - Don't Repeat Yourself) ==========
    
    def _execute(self, sql, params=()):
        """Для INSERT/UPDATE/DELETE - выполняет и автоматически коммитит"""
        with self.conn.cursor() as cur:
            cur.execute(sql, params)
            self.conn.commit()

    def _fetchall(self, sql, params=()):
        """Для SELECT - возвращает ВСЕ строки результата"""
        with self.conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()

    def _fetchone(self, sql, params=()):
        """Для SELECT - возвращает ТОЛЬКО ПЕРВУЮ строку"""
        with self.conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchone()

    # ========== 1. ПРОДВИНУТЫЙ CSV ИМПОРТ (UPSERT логика) ==========
    
    def import_csv(self, filename):
        """
        ЛОГИКА: 
        1. Читает CSV построчно
        2. Для каждого контакта проверяет - существует ли уже такой
        3. Если существует - ОБНОВЛЯЕТ (email, birthday)
        4. Если нет - СОЗДАЕТ новый
        5. Телефоны добавляются только если их еще нет (дедупликация)
        
        ПРОДВИНУТЫЕ ФИЧИ:
        - COALESCE: обновляет только те поля, которые не пустые в CSV
        - Обработка ошибок даты: если формат неправильный - пропускает, но продолжает
        - Транзакционность: при любой ошибке весь импорт откатывается
        - Вызов хранимой процедуры move_to_group() для назначения группы
        """
        if not os.path.exists(filename):
            print(f"File {filename} not found.")
            return
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Парсим поля с защитой от пустых значений
                    name = row.get('name', '').strip()
                    email = row.get('email', '').strip() or None
                    birthday = row.get('birthday', '').strip() or None
                    group = row.get('group', '').strip() or None
                    phone = row.get('phone', '').strip()
                    phone_type = row.get('phone_type', 'mobile').strip().lower()

                    if not name or not phone:
                        print(f"Skipping incomplete row: {row}")
                        continue

                    # Конвертация даты (ISO формат YYYY-MM-DD)
                    if birthday:
                        try:
                            birthday = datetime.strptime(birthday, '%Y-%m-%d').date()
                        except ValueError:
                            print(f"Invalid birthday format for {name}, skipping birthday.")
                            birthday = None

                    # ===== UPSERT ЛОГИКА: Update или Insert =====
                    with self.conn.cursor() as cur:
                        # Проверка существования по уникальному полю 'name'
                        cur.execute("SELECT id FROM contacts WHERE name = %s", (name,))
                        existing = cur.fetchone()
                        
                        if not existing:
                            # INSERT нового контакта
                            cur.execute("""
                                INSERT INTO contacts (name, email, birthday)
                                VALUES (%s, %s, %s) RETURNING id
                            """, (name, email, birthday))
                            contact_id = cur.fetchone()[0]
                        else:
                            # UPDATE существующего: COALESCE сохраняет старые значения если новое NULL
                            contact_id = existing[0]
                            cur.execute("""
                                UPDATE contacts SET email = COALESCE(%s, email),
                                                      birthday = COALESCE(%s, birthday)
                                WHERE id = %s
                            """, (email, birthday, contact_id))

                        # ДЕДУПЛИКАЦИЯ ТЕЛЕФОНОВ: добавляем только если такого номера еще нет
                        cur.execute("SELECT 1 FROM phones WHERE contact_id = %s AND phone = %s", (contact_id, phone))
                        if not cur.fetchone():
                            cur.execute("""
                                INSERT INTO phones (contact_id, phone, type)
                                VALUES (%s, %s, %s)
                            """, (contact_id, phone, phone_type))

                        # ВЫЗОВ ХРАНИМОЙ ПРОЦЕДУРЫ (бизнес-логика на стороне БД)
                        if group:
                            try:
                                cur.execute("CALL move_to_group(%s, %s)", (name, group))
                            except Exception as e:
                                print(f"Group assignment error for {name}: {e}")

                    self.conn.commit()  # ЯВНЫЙ КОММИТ после каждого контакта
                    print(f"Imported/updated: {name}")
            print("CSV import finished.")
        except Exception as e:
            self.conn.rollback()  # ОТКАТ при любой ошибке
            print(f"CSV import failed: {e}")

    # ========== 2. JSON ЭКСПОРТ (агрегация данных) ==========
    
    def export_json(self, filename):
        """
        ЛОГИКА: 
        Собирает все данные о контактах (включая телефоны и группы) в один JSON файл
        
        ПРОДВИНУТЫЕ ФИЧИ:
        - json_agg() - функция PostgreSQL для агрегации телефонов в JSON массив
        - json_build_object() - создает JSON объект для каждого телефона
        - Вложенная структура: контакт -> массив телефонов
        """
        sql = """
            SELECT c.name, c.email, c.birthday, g.name as group_name,
                   json_agg(  -- АГРЕГАЦИЯ: создает JSON массив из всех телефонов
                       json_build_object('phone', p.phone, 'type', p.type)  -- КАЖДЫЙ ТЕЛЕФОН → JSON объект
                   ) as phones
            FROM contacts c
            LEFT JOIN groups g ON c.group_id = g.id
            LEFT JOIN phones p ON c.id = p.contact_id
            GROUP BY c.id, c.name, c.email, c.birthday, g.name
            ORDER BY c.name
        """
        rows = self._fetchall(sql)
        contacts_list = []
        for row in rows:
            contact = {
                "name": row[0],
                "email": row[1],
                "birthday": str(row[2]) if row[2] else None,
                "group": row[3],
                "phones": row[4] or []   # Если нет телефонов - пустой массив
            }
            contacts_list.append(contact)

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(contacts_list, f, indent=2, ensure_ascii=False)
        print(f"Exported {len(contacts_list)} contacts to {filename}")

    # ========== 3. JSON ИМПОРТ (интерактивное разрешение конфликтов) ==========
    
    def import_json(self, filename):
        """
        ЛОГИКА:
        1. Загружает JSON
        2. Для каждого контакта проверяет существование
        3. Если существует - СПРАШИВАЕТ пользователя: перезаписать или пропустить?
        4. При перезаписи - удаляет старые телефоны и добавляет новые
        5. Назначает группы через хранимую процедуру
        
        ПРОДВИНУТЫЕ ФИЧИ:
        - ИНТЕРАКТИВНОСТЬ: пользователь сам решает судьбу дубликатов
        - АТОМАРНОСТЬ: каждый контакт обрабатывается в своей транзакции
        - КАСКАДНОЕ УДАЛЕНИЕ: при перезаписи полностью заменяет все данные
        """
        if not os.path.exists(filename):
            print(f"File {filename} not found.")
            return
        with open(filename, 'r', encoding='utf-8') as f:
            contacts_data = json.load(f)

        for contact in contacts_data:
            name = contact.get('name')
            if not name:
                continue
                
            # Проверка существования
            exists = self._fetchone("SELECT id FROM contacts WHERE name = %s", (name,))
            if exists:
                # ИНТЕРАКТИВНОЕ РАЗРЕШЕНИЕ КОНФЛИКТА
                ans = input(f"Contact '{name}' already exists. Overwrite? (y/n): ").strip().lower()
                if ans != 'y':
                    print(f"Skipping {name}")
                    continue
                # Перезапись: сначала удаляем старые телефоны
                with self.conn.cursor() as cur:
                    cur.execute("DELETE FROM phones WHERE contact_id = %s", (exists[0],))
                    cur.execute("""
                        UPDATE contacts
                        SET email = %s, birthday = %s, group_id = NULL
                        WHERE id = %s
                    """, (contact.get('email'), contact.get('birthday'), exists[0]))
                    self.conn.commit()
                contact_id = exists[0]
            else:
                # Новый контакт
                with self.conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO contacts (name, email, birthday)
                        VALUES (%s, %s, %s) RETURNING id
                    """, (name, contact.get('email'), contact.get('birthday')))
                    contact_id = cur.fetchone()[0]
                    self.conn.commit()

            # Добавление телефонов (вызов процедуры для каждого)
            for phone_obj in contact.get('phones', []):
                phone = phone_obj.get('phone')
                ptype = phone_obj.get('type', 'mobile')
                if phone:
                    try:
                        with self.conn.cursor() as cur:
                            cur.execute("CALL add_phone(%s, %s, %s)", (name, phone, ptype))
                            self.conn.commit()
                    except Exception as e:
                        print(f"Could not add phone {phone} for {name}: {e}")
                        self.conn.rollback()

            # Назначение группы
            group_name = contact.get('group')
            if group_name:
                try:
                    with self.conn.cursor() as cur:
                        cur.execute("CALL move_to_group(%s, %s)", (name, group_name))
                        self.conn.commit()
                except Exception as e:
                    print(f"Group assignment failed for {name}: {e}")
                    self.conn.rollback()
            print(f"Processed: {name}")

    # ========== 4. ФИЛЬТРАЦИЯ ПО ГРУППЕ ==========
    
    def filter_by_group(self):
        """
        ЛОГИКА: Показывает все контакты из выбранной группы
        Использует array_agg() для группировки телефонов в массив
        """
        group_name = input("Enter group name (Family, Work, Friend, Other): ").strip()
        sql = """
            SELECT c.name, c.email, c.birthday, g.name, array_agg(p.phone)  -- array_agg: собирает телефоны в массив
            FROM contacts c
            LEFT JOIN groups g ON c.group_id = g.id
            LEFT JOIN phones p ON c.id = p.contact_id
            WHERE g.name = %s
            GROUP BY c.id, c.name, c.email, c.birthday, g.name
            ORDER BY c.name
        """
        rows = self._fetchall(sql, (group_name,))
        if not rows:
            print(f"No contacts in group '{group_name}'.")
        else:
            for row in rows:
                phones = ', '.join(row[4]) if row[4] else ''
                print(f"{row[0]} | {row[1]} | {row[2]} | Group: {row[3]} | Phones: {phones}")

    # ========== 5. ПОИСК ПО EMAIL (ILIKE - регистронезависимый) ==========
    
    def search_by_email(self):
        """
        ЛОГИКА: Поиск по части email адреса
        ILIKE - PostgreSQL оператор для регистронезависимого поиска
        """
        pattern = input("Enter email pattern (e.g., @gmail.com): ").strip()
        sql = "SELECT name, email FROM contacts WHERE email ILIKE %s ORDER BY name"
        rows = self._fetchall(sql, (f"%{pattern}%",))
        if rows:
            for name, email in rows:
                print(f"{name} -> {email}")
        else:
            print("No matching emails.")

    # ========== 6. ДИНАМИЧЕСКАЯ СОРТИРОВКА (с обработкой NULL) ==========
    
    def sorted_list(self):
        """
        ЛОГИКА: Пользователь выбирает поле для сортировки, SQL формируется динамически
        
        ПРОДВИНУТЫЕ ФИЧИ:
        - NULLS LAST: контакты без даты рождения идут в конце списка
        - Динамический ORDER BY: строка запроса меняется в зависимости от выбора
        """
        print("Sort by: 1. Name  2. Birthday  3. Date added (created_at)")
        choice = input("Choice: ").strip()
        if choice == '1':
            order = "c.name"
        elif choice == '2':
            order = "c.birthday NULLS LAST"  # NULLS LAST - пустые даты в конец
        elif choice == '3':
            order = "c.created_at"
        else:
            print("Invalid choice.")
            return

        # ДИНАМИЧЕСКОЕ ФОРМИРОВАНИЕ SQL (безопасно, т.к. choice проверен)
        sql = f"""
            SELECT c.name, c.email, c.birthday, g.name, array_agg(p.phone), c.created_at
            FROM contacts c
            LEFT JOIN groups g ON c.group_id = g.id
            LEFT JOIN phones p ON c.id = p.contact_id
            GROUP BY c.id, c.name, c.email, c.birthday, g.name, c.created_at
            ORDER BY {order}
        """
        rows = self._fetchall(sql)
        for row in rows:
            phones = ', '.join(row[4]) if row[4] else ''
            print(f"{row[0]} | {row[1]} | {row[2]} | Group: {row[3]} | Phones: {phones} | Added: {row[5]}")

    # ========== 7. ПОСТРАНИЧНАЯ НАВИГАЦИЯ (server-side пагинация) ==========
    
    def paginated_navigation(self, page_size=5):
        """
        ЛОГИКА: Просмотр контактов страницами, используя функцию PostgreSQL
        
        ПРОДВИНУТЫЕ ФИЧИ:
        - Server-side пагинация: LIMIT и OFFSET выполняются на стороне БД
        - НЕ ЗАГРУЖАЕТ все данные в память (экономия ресурсов)
        - Функция get_contacts_paginated() возвращает ТОЛЬКО нужную страницу
        - Stateful навигация: сохраняет текущую позицию (offset)
        """
        offset = 0  # ТЕКУЩАЯ ПОЗИЦИЯ (хранится в памяти, не в БД)
        while True:
            # ВЫЗОВ ФУНКЦИИ БД: передаем размер страницы и смещение
            sql = "SELECT * FROM get_contacts_paginated(%s, %s)"
            rows = self._fetchall(sql, (page_size, offset))
            if not rows:
                print("No more contacts.")
                break
            print(f"\n--- Page (offset {offset}) ---")
            for r in rows:
                print(f"ID: {r[0]}, Name: {r[1]}, Email: {r[2]}, Birthday: {r[3]}, Group: {r[4]}")
                if r[5]:
                    print(f"   Phones: {', '.join(r[5])}")
                print("-" * 40)
            
            # НАВИГАЦИЯ: изменяем offset пользовательскими командами
            cmd = input("Next page (n), Previous (p), Quit (q): ").strip().lower()
            if cmd == 'n':
                offset += page_size   # Следующая страница
            elif cmd == 'p' and offset >= page_size:
                offset -= page_size   # Предыдущая страница
            elif cmd == 'q':
                break
            else:
                print("Continuing...")

    # ========== 8. ДОБАВЛЕНИЕ ТЕЛЕФОНА (хранимая процедура add_phone) ==========
    
    def add_phone_interactive(self):
        """
        ЛОГИКА: Вызывает хранимую процедуру add_phone() для добавления телефона
        
        ПРЕИМУЩЕСТВА ХРАНИМЫХ ПРОЦЕДУР:
        - Проверка существования контакта на стороне БД
        - Автоматическая дедупликация телефонов
        - Единая бизнес-логика для всех приложений
        """
        name = input("Contact name: ").strip()
        phone = input("Phone number: ").strip()
        ptype = input("Type (home/work/mobile): ").strip().lower()
        try:
            with self.conn.cursor() as cur:
                cur.execute("CALL add_phone(%s, %s, %s)", (name, phone, ptype))
                self.conn.commit()
                print("Phone added successfully.")
        except Exception as e:
            self.conn.rollback()
            print(f"Error: {e}")

    # ========== 9. ПЕРЕМЕЩЕНИЕ В ГРУППУ (хранимая процедура move_to_group) ==========
    
    def move_to_group_interactive(self):
        """
        ЛОГИКА: Вызывает хранимую процедуру move_to_group()
        
        ЧТО ДЕЛАЕТ ПРОЦЕДУРА:
        - Проверяет существование контакта
        - Автоматически создает группу, если ее нет
        - Обновляет group_id у контакта
        """
        name = input("Contact name: ").strip()
        group = input("Group name: ").strip()
        try:
            with self.conn.cursor() as cur:
                cur.execute("CALL move_to_group(%s, %s)", (name, group))
                self.conn.commit()
                print(f"Contact {name} moved to group {group}.")
        except Exception as e:
            self.conn.rollback()
            print(f"Error: {e}")

    # ========== 10. ПОЛНОТЕКСТОВЫЙ ПОИСК (функция search_contacts) ==========
    
    def search_contacts_interactive(self):
        """
        ЛОГИКА: Поиск по имени, email или телефону через функцию БД
        
        ПРОДВИНУТЫЕ ФИЧИ:
        - Функция search_contacts() ищет СРАЗУ в трех полях (name, email, phone)
        - Возвращает структурированный результат (контакт + все его телефоны)
        - Регистронезависимый поиск (ILIKE внутри функции)
        """
        query = input("Enter search pattern (name, email, phone): ").strip()
        rows = self._fetchall("SELECT * FROM search_contacts(%s)", (query,))
        if not rows:
            print("No matches found.")
        else:
            for r in rows:
                phones_str = ', '.join(r[5]) if r[5] else ''
                print(f"ID: {r[0]}, Name: {r[1]}, Email: {r[2]}, Birthday: {r[3]}, Group: {r[4]}")
                print(f"   Phones: {phones_str}, Added: {r[6]}")
                print("---")

    # ========== ГЛАВНОЕ МЕНЮ (точка входа в приложение) ==========
    
    def run(self):
        """
        ЛОГИКА: Бесконечный цикл с обработкой пользовательского ввода
        Каждый пункт меню вызывает соответствующий метод класса
        """
        while True:
            print("\n===== PHONEBOOK EXTENDED =====")
            print("1. Import from CSV (extended)")
            print("2. Export to JSON")
            print("3. Import from JSON")
            print("4. Filter by group")
            print("5. Search by email")
            print("6. Sorted list (name/birthday/date)")
            print("7. Paginated navigation")
            print("8. Add phone to contact")
            print("9. Move contact to group")
            print("10. Full-text search (name, email, phone)")
            print("0. Exit")
            choice = input("Your choice: ").strip()

            if choice == '1':
                fn = input("CSV filename: ").strip()
                self.import_csv(fn)
            elif choice == '2':
                fn = input("JSON filename to export: ").strip()
                self.export_json(fn)
            elif choice == '3':
                fn = input("JSON filename to import: ").strip()
                self.import_json(fn)
            elif choice == '4':
                self.filter_by_group()
            elif choice == '5':
                self.search_by_email()
            elif choice == '6':
                self.sorted_list()
            elif choice == '7':
                size = input("Page size (default 5): ").strip()
                size = int(size) if size.isdigit() else 5
                self.paginated_navigation(size)
            elif choice == '8':
                self.add_phone_interactive()
            elif choice == '9':
                self.move_to_group_interactive()
            elif choice == '10':
                self.search_contacts_interactive()
            elif choice == '0':
                break
            else:
                print("Invalid option.")

# ========== ТОЧКА ВХОДА ==========
if __name__ == "__main__":
    app = PhoneBookExtended()  # Создаем объект (устанавливается соединение с БД)
    try:
        app.run()  # Запускаем главный цикл
    finally:
        app.close()  # ОБЯЗАТЕЛЬНО: закрываем соединение (даже если была ошибка)
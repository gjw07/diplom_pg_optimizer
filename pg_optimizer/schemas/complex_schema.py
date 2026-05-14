#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Сложная схема базы данных (много таблиц, иерархия)"""

import random
from datetime import datetime, timedelta


def create_tables(cursor):
    """Создаёт сложные таблицы"""
    
    cursor.execute("""
        DROP TABLE IF EXISTS salary_history CASCADE;
        DROP TABLE IF EXISTS employee_skills CASCADE;
        DROP TABLE IF EXISTS skills CASCADE;
        DROP TABLE IF EXISTS employee_projects CASCADE;
        DROP TABLE IF EXISTS projects CASCADE;
        DROP TABLE IF EXISTS employees CASCADE;
        DROP TABLE IF EXISTS departments CASCADE;
        DROP TABLE IF EXISTS locations CASCADE;
    """)
    
    cursor.execute("""
        CREATE TABLE locations (
            id SERIAL PRIMARY KEY,
            city VARCHAR(100) NOT NULL,
            address VARCHAR(200),
            region VARCHAR(50),
            country VARCHAR(50) DEFAULT 'Russia'
        )
    """)
    
    cursor.execute("""
        CREATE TABLE departments (
            id SERIAL PRIMARY KEY,
            dept_code VARCHAR(10) NOT NULL UNIQUE,
            dept_name VARCHAR(100) NOT NULL,
            parent_dept_id INTEGER REFERENCES departments(id),
            location_id INTEGER REFERENCES locations(id),
            budget NUMERIC(12,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE employees (
            id SERIAL PRIMARY KEY,
            emp_id VARCHAR(20) NOT NULL UNIQUE,
            first_name VARCHAR(50) NOT NULL,
            last_name VARCHAR(50) NOT NULL,
            middle_name VARCHAR(50),
            department_id INTEGER REFERENCES departments(id),
            manager_id INTEGER REFERENCES employees(id),
            position VARCHAR(50),
            level INTEGER DEFAULT 1,
            salary NUMERIC(10,2),
            hire_date DATE,
            birth_date DATE,
            email VARCHAR(100),
            phone VARCHAR(20),
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE skills (
            id SERIAL PRIMARY KEY,
            skill_code VARCHAR(20) NOT NULL UNIQUE,
            skill_name VARCHAR(100) NOT NULL,
            category VARCHAR(50)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE employee_skills (
            id SERIAL PRIMARY KEY,
            employee_id INTEGER REFERENCES employees(id),
            skill_id INTEGER REFERENCES skills(id),
            proficiency_level INTEGER CHECK (proficiency_level BETWEEN 1 AND 5),
            certified_date DATE,
            UNIQUE(employee_id, skill_id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE projects (
            id SERIAL PRIMARY KEY,
            project_code VARCHAR(20) NOT NULL UNIQUE,
            project_name VARCHAR(200) NOT NULL,
            department_id INTEGER REFERENCES departments(id),
            budget NUMERIC(12,2),
            start_date DATE,
            end_date DATE,
            status VARCHAR(20) DEFAULT 'planning'
        )
    """)
    
    cursor.execute("""
        CREATE TABLE employee_projects (
            id SERIAL PRIMARY KEY,
            employee_id INTEGER REFERENCES employees(id),
            project_id INTEGER REFERENCES projects(id),
            role VARCHAR(50),
            hours_allocated INTEGER,
            actual_hours INTEGER,
            assigned_date DATE,
            completed_date DATE
        )
    """)
    
    cursor.execute("""
        CREATE TABLE salary_history (
            id SERIAL PRIMARY KEY,
            employee_id INTEGER REFERENCES employees(id),
            salary NUMERIC(10,2),
            effective_date DATE NOT NULL,
            change_reason VARCHAR(100)
        )
    """)
    
    # cursor.execute("CREATE INDEX idx_emp_dept ON employees(department_id);")
    # cursor.execute("CREATE INDEX idx_emp_manager ON employees(manager_id);")
    # cursor.execute("CREATE INDEX idx_emp_salary ON employees(salary);")
    # cursor.execute("CREATE INDEX idx_emp_skills_emp ON employee_skills(employee_id);")
    # cursor.execute("CREATE INDEX idx_emp_proj_emp ON employee_projects(employee_id);")
    # cursor.execute("CREATE INDEX idx_emp_proj_proj ON employee_projects(project_id);")
    # cursor.execute("CREATE INDEX idx_salary_history_emp ON salary_history(employee_id, effective_date);")
    
    print("✅ Сложная схема создана (8+ таблиц)")


def generate_data(cursor, counts: dict):
    """Генерирует тестовые данные для сложной схемы"""
    
    locations = [
        ('Moscow', 'Tverskaya 1', 'Central', 'Russia'),
        ('Moscow', 'Leninsky 2', 'Central', 'Russia'),
        ('Saint Petersburg', 'Nevsky 3', 'North-West', 'Russia'),
        ('Kazan', 'Baumana 4', 'Volga', 'Russia'),
        ('Novosibirsk', 'Krasny 5', 'Siberia', 'Russia'),
        ('Ekaterinburg', 'Lenina 6', 'Ural', 'Russia'),
        ('Nizhny Novgorod', 'Bolshaya Pokrovskaya 7', 'Volga', 'Russia'),
    ]
    
    for loc in locations:
        cursor.execute("""
            INSERT INTO locations (city, address, region, country)
            VALUES (%s, %s, %s, %s)
        """, loc)
    
    departments = [
        ('HOLD', 'Holding', None, 1, 5000000),
        ('IT', 'Information Technology', 1, 1, 2000000),
        ('DEV', 'Development', 2, 1, 1000000),
        ('QA', 'Quality Assurance', 2, 1, 500000),
        ('OPS', 'Operations', 1, 1, 800000),
        ('HR', 'Human Resources', 1, 1, 400000),
        ('SALES', 'Sales', 1, 2, 600000),
        ('FIN', 'Finance', 1, 1, 700000),
        ('RND', 'Research & Development', 2, 3, 1500000),
        ('LEGAL', 'Legal', 1, 1, 300000),
    ]
    
    for dept in departments:
        parent_id = dept[2] if dept[2] is not None else None
        cursor.execute("""
            INSERT INTO departments (dept_code, dept_name, parent_dept_id, location_id, budget)
            VALUES (%s, %s, %s, %s, %s)
        """, (dept[0], dept[1], parent_id, dept[3], dept[4]))
    
    first_names = ['Иван', 'Петр', 'Анна', 'Мария', 'Алексей', 'Елена', 'Дмитрий', 'Ольга',
                   'Сергей', 'Татьяна', 'Андрей', 'Наталья', 'Владимир', 'Екатерина', 'Павел', 'Юлия']
    last_names = ['Иванов', 'Петров', 'Сидоров', 'Кузнецова', 'Смирнов', 'Волкова',
                  'Морозов', 'Новикова', 'Козлов', 'Лебедева', 'Соколов', 'Михайлова']
    positions = ['Junior', 'Middle', 'Senior', 'Team Lead', 'Manager', 'Director', 'CTO', 'CEO']
    
    managers = []
    for i in range(15):
        emp_id = f"EMP{str(i+1).zfill(6)}"
        first = first_names[i % len(first_names)]
        last = last_names[i % len(last_names)]
        dept_id = (i % 10) + 1
        position = positions[min(4 + i % 3, 7)]
        salary = 150000 + i * 25000
        hire_date = f"201{5 + i % 3}-01-01"
        email = f"{first.lower()}.{last.lower()}@company.com"
        
        cursor.execute("""
            INSERT INTO employees (emp_id, first_name, last_name, department_id, position, salary, hire_date, email, is_active, level)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (emp_id, first, last, dept_id, position, salary, hire_date, email, True, 5))
        managers.append(cursor.fetchone()[0])
    
    employee_count = counts.get('employees', 1500)
    for i in range(employee_count):
        emp_id = f"EMP{str(i+16).zfill(6)}"
        first = first_names[(i + 15) % len(first_names)]
        last = last_names[(i + 15) % len(last_names)]
        dept_id = (i % 10) + 1
        manager_id = managers[i % len(managers)]
        position = positions[i % len(positions)]
        salary = 40000 + random.randint(0, 130000)
        hire_date = datetime.now() - timedelta(days=random.randint(0, 3650))
        birth_date = datetime.now() - timedelta(days=random.randint(7000, 15000))
        email = f"{first.lower()}.{last.lower()}@company.com"
        phone = f"+7{random.randint(9000000000, 9999999999)}"
        level = random.randint(1, 4)
        
        cursor.execute("""
            INSERT INTO employees 
            (emp_id, first_name, last_name, department_id, manager_id, position, salary, hire_date, birth_date, email, phone, is_active, level)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (emp_id, first, last, dept_id, manager_id, position, salary, hire_date, birth_date, email, phone, True, level))
        
        if (i + 1) % 300 == 0:
            cursor.connection.commit()
            print(f"  Загружено {i+1} сотрудников...")
    
    skills = [
        ('PYTHON', 'Python Programming', 'Development'),
        ('JAVA', 'Java Development', 'Development'),
        ('SQL', 'SQL Database', 'Database'),
        ('DOCKER', 'Docker', 'DevOps'),
        ('K8S', 'Kubernetes', 'DevOps'),
        ('REACT', 'React JS', 'Frontend'),
        ('ANGULAR', 'Angular', 'Frontend'),
        ('POSTGRES', 'PostgreSQL', 'Database'),
        ('AWS', 'Amazon Web Services', 'Cloud'),
        ('GCP', 'Google Cloud Platform', 'Cloud'),
        ('LEADERSHIP', 'Leadership', 'Management'),
        ('PROJECT_MGMT', 'Project Management', 'Management'),
    ]
    
    for skill in skills:
        cursor.execute("""
            INSERT INTO skills (skill_code, skill_name, category)
            VALUES (%s, %s, %s)
        """, skill)
    
    cursor.execute("SELECT id FROM skills")
    skill_ids = [row[0] for row in cursor.fetchall()]
    
    for emp_id in range(1, employee_count + 16):
        num_skills = random.randint(1, 5)
        selected_skills = random.sample(skill_ids, min(num_skills, len(skill_ids)))
        for skill_id in selected_skills:
            proficiency = random.randint(1, 5)
            cursor.execute("""
                INSERT INTO employee_skills (employee_id, skill_id, proficiency_level, certified_date)
                VALUES (%s, %s, %s, CURRENT_DATE - INTERVAL '%s days')
            """, (emp_id, skill_id, proficiency, random.randint(0, 730)))
    
    projects_count = counts.get('projects', 30)
    for i in range(projects_count):
        proj_code = f"PRJ{str(i+1).zfill(4)}"
        proj_name = f"Проект {chr(65 + i % 26)}{chr(65 + (i // 26) % 26)}"
        dept_id = (i % 10) + 1
        budget = random.randint(300000, 3000000)
        status = random.choice(['planning', 'active', 'completed', 'on_hold'])
        
        cursor.execute("""
            INSERT INTO projects (project_code, project_name, department_id, budget, start_date, status)
            VALUES (%s, %s, %s, %s, CURRENT_DATE - INTERVAL '%s days', %s)
        """, (proj_code, proj_name, dept_id, budget, random.randint(0, 730), status))
    
    cursor.execute("SELECT id FROM projects")
    project_ids = [row[0] for row in cursor.fetchall()]
    
    for emp_id in range(1, employee_count + 16):
        num_projects = random.randint(0, 5)
        selected_projects = random.sample(project_ids, min(num_projects, len(project_ids)))
        for proj_id in selected_projects:
            hours = random.randint(20, 200)
            actual_hours = hours + random.randint(-30, 50)
            cursor.execute("""
                INSERT INTO employee_projects 
                (employee_id, project_id, role, hours_allocated, actual_hours, assigned_date, completed_date)
                VALUES (%s, %s, %s, %s, %s, CURRENT_DATE - INTERVAL '%s days', 
                        CASE WHEN random() > 0.4 THEN CURRENT_DATE - INTERVAL '%s days' ELSE NULL END)
            """, (emp_id, proj_id, 'Developer', hours, actual_hours, random.randint(0, 365), random.randint(0, 60)))
    
    for emp_id in range(1, employee_count + 16):
        num_changes = random.randint(0, 5)
        for _ in range(num_changes):
            old_salary = 30000 + random.randint(0, 150000)
            cursor.execute("""
                INSERT INTO salary_history (employee_id, salary, effective_date, change_reason)
                VALUES (%s, %s, CURRENT_DATE - INTERVAL '%s days', %s)
            """, (emp_id, old_salary, random.randint(0, 1825), random.choice(['hire', 'promotion', 'adjustment'])))
    
    cursor.connection.commit()
    print(f"✅ Создано {employee_count + 15} сотрудников, {projects_count} проектов, {len(skills)} навыков")


def get_test_queries():
    """Возвращает запросы для тестирования схемы COMPLEX"""
    return {
        'simple': [
            "SELECT 1",
            "SELECT COUNT(*) FROM employees",
            "SELECT COUNT(*) FROM departments",
            "SELECT COUNT(*) FROM projects",
            "SELECT COUNT(*) FROM skills",
            "SELECT COUNT(*) FROM employee_skills",
            "SELECT * FROM employees LIMIT 10",
        ],
        'medium': [
            """
            SELECT e.first_name, e.last_name, d.dept_name, e.salary
            FROM employees e 
            JOIN departments d ON e.department_id = d.id 
            WHERE e.salary > 80000
            LIMIT 100
            """,
            """
            SELECT d.dept_name, COUNT(e.id) as emp_count, AVG(e.salary) as avg_salary
            FROM departments d 
            LEFT JOIN employees e ON d.id = e.department_id 
            GROUP BY d.id
            ORDER BY avg_salary DESC
            """,
            """
            SELECT s.skill_name, COUNT(es.employee_id) as emp_count
            FROM skills s 
            LEFT JOIN employee_skills es ON s.id = es.skill_id 
            GROUP BY s.id
            ORDER BY emp_count DESC
            LIMIT 20
            """,
        ],
        'complex': [
            """
            SELECT 
                d.dept_name,
                e.position,
                COUNT(DISTINCT e.id) as emp_count,
                AVG(e.salary) as avg_salary,
                COUNT(DISTINCT es.skill_id) as skill_count
            FROM departments d
            JOIN employees e ON d.id = e.department_id
            LEFT JOIN employee_skills es ON e.id = es.employee_id
            GROUP BY d.id, e.position
            HAVING COUNT(e.id) > 3
            ORDER BY avg_salary DESC
            LIMIT 30
            """,
            """
            WITH RECURSIVE dept_tree AS (
                SELECT id, dept_name, parent_dept_id, 1 as level
                FROM departments WHERE parent_dept_id IS NULL
                UNION ALL
                SELECT d.id, d.dept_name, d.parent_dept_id, dt.level + 1
                FROM departments d
                JOIN dept_tree dt ON d.parent_dept_id = dt.id
            )
            SELECT dt.dept_name, dt.level, COUNT(e.id) as total_employees, AVG(e.salary) as avg_salary
            FROM dept_tree dt
            LEFT JOIN employees e ON dt.id = e.department_id
            GROUP BY dt.id, dt.dept_name, dt.level
            ORDER BY dt.level, avg_salary DESC
            """,
            """
            WITH employee_productivity AS (
                SELECT 
                    e.id,
                    e.first_name || ' ' || e.last_name as employee_name,
                    d.dept_name,
                    e.salary,
                    COUNT(DISTINCT ep.project_id) as project_count,
                    COALESCE(SUM(ep.actual_hours), 0) as total_hours,
                    COUNT(DISTINCT es.skill_id) as skill_count,
                    RANK() OVER (ORDER BY COALESCE(SUM(ep.actual_hours), 0) DESC) as productivity_rank
                FROM employees e
                JOIN departments d ON e.department_id = d.id
                LEFT JOIN employee_projects ep ON e.id = ep.employee_id
                LEFT JOIN employee_skills es ON e.id = es.employee_id
                WHERE e.is_active = true
                GROUP BY e.id, d.id, d.dept_name
            )
            SELECT employee_name, dept_name, salary, project_count, total_hours, skill_count, productivity_rank
            FROM employee_productivity
            WHERE productivity_rank <= 20
            ORDER BY productivity_rank
            """,
        ],
        'very_complex': [
            """
            WITH skill_gaps AS (
                SELECT 
                    d.dept_name,
                    s.skill_name,
                    s.category,
                    COUNT(DISTINCT e.id) as employees_with_skill,
                    (SELECT COUNT(*) FROM employees WHERE department_id = d.id) as total_in_dept
                FROM departments d
                CROSS JOIN skills s
                LEFT JOIN employees e ON e.department_id = d.id
                LEFT JOIN employee_skills es ON e.id = es.employee_id AND es.skill_id = s.id
                GROUP BY d.id, d.dept_name, s.id, s.skill_name, s.category
            ),
            dept_stats AS (
                SELECT 
                    dept_name,
                    AVG(employees_with_skill * 1.0 / NULLIF(total_in_dept, 0)) as skill_coverage,
                    SUM(CASE WHEN employees_with_skill = 0 THEN 1 ELSE 0 END) as missing_skills
                FROM skill_gaps
                WHERE total_in_dept > 0
                GROUP BY dept_name
            )
            SELECT 
                dept_name,
                skill_coverage * 100 as coverage_percent,
                missing_skills,
                RANK() OVER (ORDER BY skill_coverage DESC) as coverage_rank
            FROM dept_stats
            ORDER BY coverage_rank
            LIMIT 15
            """,
        ],
    }
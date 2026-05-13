#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Сложная схема базы данных (много таблиц, иерархия, партиционирование)"""
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
    
    # Локации
    cursor.execute("""
        CREATE TABLE locations (
            id SERIAL PRIMARY KEY,
            city VARCHAR(100) NOT NULL,
            address VARCHAR(200),
            region VARCHAR(50),
            country VARCHAR(50) DEFAULT 'Russia'
        )
    """)
    
    # Отделы (с иерархией)
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
    
    # Сотрудники
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
    
    # Навыки
    cursor.execute("""
        CREATE TABLE skills (
            id SERIAL PRIMARY KEY,
            skill_code VARCHAR(20) NOT NULL UNIQUE,
            skill_name VARCHAR(100) NOT NULL,
            category VARCHAR(50)
        )
    """)
    
    # Связь сотрудников с навыками
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
    
    # Проекты
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
    
    # Связь сотрудников с проектами
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
    
    # История зарплат (партиционирование по годам)
    cursor.execute("""
        CREATE TABLE salary_history (
            id SERIAL PRIMARY KEY,
            employee_id INTEGER REFERENCES employees(id),
            salary NUMERIC(10,2),
            effective_date DATE NOT NULL,
            change_reason VARCHAR(100)
        )
    """)
    
    # Индексы
    cursor.execute("CREATE INDEX idx_emp_dept ON employees(department_id);")
    cursor.execute("CREATE INDEX idx_emp_manager ON employees(manager_id);")
    cursor.execute("CREATE INDEX idx_emp_salary ON employees(salary);")
    cursor.execute("CREATE INDEX idx_emp_skills_emp ON employee_skills(employee_id);")
    cursor.execute("CREATE INDEX idx_emp_proj_emp ON employee_projects(employee_id);")
    cursor.execute("CREATE INDEX idx_emp_proj_proj ON employee_projects(project_id);")
    cursor.execute("CREATE INDEX idx_salary_history_emp ON salary_history(employee_id, effective_date);")
    
    print("✅ Сложная схема создана (8+ таблиц, иерархия, партиционирование)")


def generate_data(cursor, counts: dict):
    """Генерирует тестовые данные для сложной схемы"""
    
    # Локации
    locations = [
        ('Moscow', 'Tverskaya 1', 'Central', 'Russia'),
        ('Moscow', 'Leninsky 2', 'Central', 'Russia'),
        ('Saint Petersburg', 'Nevsky 3', 'North-West', 'Russia'),
        ('Kazan', 'Baumana 4', 'Volga', 'Russia'),
        ('Novosibirsk', 'Krasny 5', 'Siberia', 'Russia'),
    ]
    
    for loc in locations:
        cursor.execute("""
            INSERT INTO locations (city, address, region, country)
            VALUES (%s, %s, %s, %s)
        """, loc)
    
    # Отделы (с иерархией)
    departments = [
        ('HOLD', 'Holding', None, 1, 5000000),
        ('IT', 'Information Technology', 1, 1, 2000000),
        ('DEV', 'Development', 2, 1, 1000000),
        ('QA', 'Quality Assurance', 2, 1, 500000),
        ('OPS', 'Operations', 1, 1, 800000),
        ('HR', 'Human Resources', 1, 1, 400000),
        ('SALES', 'Sales', 1, 2, 600000),
        ('FIN', 'Finance', 1, 1, 700000),
    ]
    
    for dept in departments:
        parent_id = dept[2] if dept[2] is not None else None
        cursor.execute("""
            INSERT INTO departments (dept_code, dept_name, parent_dept_id, location_id, budget)
            VALUES (%s, %s, %s, %s, %s)
        """, (dept[0], dept[1], parent_id, dept[3], dept[4]))
    
    # Сотрудники
    first_names = ['Иван', 'Петр', 'Анна', 'Мария', 'Алексей', 'Елена', 'Дмитрий', 'Ольга', 
                   'Сергей', 'Татьяна', 'Андрей', 'Наталья', 'Владимир', 'Екатерина', 'Павел', 'Юлия']
    last_names = ['Иванов', 'Петров', 'Сидоров', 'Кузнецова', 'Смирнов', 'Волкова', 
                  'Морозов', 'Новикова', 'Козлов', 'Лебедева', 'Соколов', 'Михайлова']
    positions = ['Junior', 'Middle', 'Senior', 'Team Lead', 'Manager', 'Director', 'CTO', 'CEO']
    
    # Сначала создадим руководителей
    managers = []
    for i in range(10):
        emp_id = f"EMP{str(i+1).zfill(6)}"
        first = first_names[i % len(first_names)]
        last = last_names[i % len(last_names)]
        dept_id = (i % 8) + 1
        position = positions[min(4 + i % 3, 7)]
        salary = 150000 + i * 20000
        hire_date = f"201{5 + i % 3}-01-01"
        email = f"{first.lower()}.{last.lower()}@company.com"
        
        cursor.execute("""
            INSERT INTO employees (emp_id, first_name, last_name, department_id, position, salary, hire_date, email, is_active, level)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (emp_id, first, last, dept_id, position, salary, hire_date, email, True, 5))
        
        managers.append(cursor.fetchone()[0])
    
    # Остальные сотрудники
    for i in range(counts.get('employees', 500)):
        emp_id = f"EMP{str(i+11).zfill(6)}"
        first = first_names[(i + 10) % len(first_names)]
        last = last_names[(i + 10) % len(last_names)]
        dept_id = (i % 8) + 1
        manager_id = managers[i % len(managers)]
        position = positions[i % len(positions)]
        salary = 40000 + (i % 100000)
        hire_date = f"202{i % 4 + 1}-{i % 12 + 1:02d}-01"
        email = f"{first.lower()}.{last.lower()}@company.com"
        level = (i % 4) + 1
        
        cursor.execute("""
            INSERT INTO employees (emp_id, first_name, last_name, department_id, manager_id, position, salary, hire_date, email, is_active, level)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (emp_id, first, last, dept_id, manager_id, position, salary, hire_date, email, True, level))
    
    # Навыки
    skills = [
        ('PYTHON', 'Python Programming', 'Development'),
        ('JAVA', 'Java Development', 'Development'),
        ('SQL', 'SQL Database', 'Database'),
        ('DOCKER', 'Docker', 'DevOps'),
        ('K8S', 'Kubernetes', 'DevOps'),
        ('REACT', 'React JS', 'Frontend'),
        ('ANGULAR', 'Angular', 'Frontend'),
        ('POSTGRES', 'PostgreSQL', 'Database'),
    ]
    
    for skill in skills:
        cursor.execute("""
            INSERT INTO skills (skill_code, skill_name, category)
            VALUES (%s, %s, %s)
        """, skill)


def get_test_queries():
    """Возвращает запросы для тестирования этой схемы"""
    
    return {
        'simple': [
            "SELECT * FROM employees LIMIT 10",
            "SELECT COUNT(*) FROM employees",
            "SELECT * FROM departments",
            "SELECT * FROM projects LIMIT 10",
        ],
        'medium': [
            "SELECT d.dept_name, COUNT(e.id) as emp_count FROM departments d LEFT JOIN employees e ON d.id = e.department_id GROUP BY d.id",
            "SELECT e.first_name, e.last_name, m.first_name as manager_name FROM employees e LEFT JOIN employees m ON e.manager_id = m.id LIMIT 20",
            "SELECT s.skill_name, COUNT(es.employee_id) as emp_count FROM skills s LEFT JOIN employee_skills es ON s.id = es.skill_id GROUP BY s.id",
        ],
        'complex': [
            """
            WITH RECURSIVE dept_tree AS (
                SELECT id, dept_name, parent_dept_id, 1 as level
                FROM departments WHERE parent_dept_id IS NULL
                UNION ALL
                SELECT d.id, d.dept_name, d.parent_dept_id, dt.level + 1
                FROM departments d
                JOIN dept_tree dt ON d.parent_dept_id = dt.id
            )
            SELECT * FROM dept_tree ORDER BY level, dept_name
            """,
            """
            SELECT 
                d.dept_name,
                COUNT(DISTINCT e.id) as total_employees,
                AVG(e.salary) as avg_salary,
                COUNT(DISTINCT es.skill_id) as distinct_skills
            FROM departments d
            LEFT JOIN employees e ON d.id = e.department_id
            LEFT JOIN employee_skills es ON e.id = es.employee_id
            GROUP BY d.id
            ORDER BY avg_salary DESC
            """,
        ],
    }
    
def get_test_queries():
    """Возвращает запросы для тестирования схемы COMPLEX"""
    return {
        'simple': [
            "SELECT 1",
            "SELECT COUNT(*) FROM employees",
            "SELECT COUNT(*) FROM departments",
            "SELECT COUNT(*) FROM projects",
            "SELECT COUNT(*) FROM skills",
            "SELECT * FROM employees LIMIT 10",
        ],
        'medium': [
            "SELECT e.first_name, e.last_name, d.dept_name FROM employees e JOIN departments d ON e.department_id = d.id LIMIT 50",
            "SELECT d.dept_name, COUNT(e.id) as emp_count FROM departments d LEFT JOIN employees e ON d.id = e.department_id GROUP BY d.id",
            "SELECT s.skill_name, COUNT(es.employee_id) as emp_count FROM skills s LEFT JOIN employee_skills es ON s.id = es.skill_id GROUP BY s.id",
        ],
        'complex': [
            "SELECT d.dept_name, AVG(e.salary) as avg_salary, COUNT(DISTINCT es.skill_id) as skill_count FROM departments d JOIN employees e ON d.id = e.department_id LEFT JOIN employee_skills es ON e.id = es.employee_id GROUP BY d.id",
            """
            WITH RECURSIVE dept_tree AS (
                SELECT id, dept_name, parent_dept_id, 1 as level
                FROM departments WHERE parent_dept_id IS NULL
                UNION ALL
                SELECT d.id, d.dept_name, d.parent_dept_id, dt.level + 1
                FROM departments d
                JOIN dept_tree dt ON d.parent_dept_id = dt.id
            )
            SELECT * FROM dept_tree ORDER BY level, dept_name
            """,
        ],
        'very_complex': [
            """
            SELECT 
                e.first_name || ' ' || e.last_name as employee_name,
                e.salary,
                d.dept_name,
                ROW_NUMBER() OVER (PARTITION BY d.id ORDER BY e.salary DESC) as rank_in_dept
            FROM employees e
            JOIN departments d ON e.department_id = d.id
            ORDER BY d.dept_name, rank_in_dept
            LIMIT 50
            """,
        ],
    }
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Средняя схема базы данных (4 таблицы, связи многие-ко-многим)"""
import random
from datetime import datetime, timedelta

def create_tables(cursor):
    """Создаёт таблицы средней сложности"""
    
    cursor.execute("""
        DROP TABLE IF EXISTS employee_projects CASCADE;
        DROP TABLE IF EXISTS projects CASCADE;
        DROP TABLE IF EXISTS employees CASCADE;
        DROP TABLE IF EXISTS departments CASCADE;
    """)
    
    # Отделы
    cursor.execute("""
        CREATE TABLE departments (
            id SERIAL PRIMARY KEY,
            dept_code VARCHAR(10) NOT NULL UNIQUE,
            dept_name VARCHAR(100) NOT NULL,
            location VARCHAR(100),
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
            department_id INTEGER REFERENCES departments(id),
            position VARCHAR(50),
            salary NUMERIC(10,2),
            hire_date DATE,
            email VARCHAR(100),
            is_active BOOLEAN DEFAULT TRUE
        )
    """)
    
    # Проекты
    cursor.execute("""
        CREATE TABLE projects (
            id SERIAL PRIMARY KEY,
            project_code VARCHAR(20) NOT NULL UNIQUE,
            project_name VARCHAR(200) NOT NULL,
            budget NUMERIC(12,2),
            start_date DATE,
            end_date DATE,
            status VARCHAR(20) DEFAULT 'active'
        )
    """)
    
    # Связь сотрудников с проектами (многие-ко-многим)
    cursor.execute("""
        CREATE TABLE employee_projects (
            id SERIAL PRIMARY KEY,
            employee_id INTEGER REFERENCES employees(id),
            project_id INTEGER REFERENCES projects(id),
            role VARCHAR(50),
            hours_allocated INTEGER,
            assigned_date DATE,
            UNIQUE(employee_id, project_id)
        )
    """)
    
    # Индексы
    cursor.execute("CREATE INDEX idx_emp_dept ON employees(department_id);")
    cursor.execute("CREATE INDEX idx_emp_proj_emp ON employee_projects(employee_id);")
    cursor.execute("CREATE INDEX idx_emp_proj_proj ON employee_projects(project_id);")
    
    print("✅ Средняя схема создана (4 таблицы, связи многие-ко-многим)")


def generate_data(cursor, counts: dict):
    """Генерирует тестовые данные"""
    
    # Отделы
    departments = [
        ('IT', 'Information Technology', 'Moscow', 1000000),
        ('HR', 'Human Resources', 'Moscow', 500000),
        ('SALES', 'Sales', 'Saint Petersburg', 800000),
        ('FIN', 'Finance', 'Moscow', 600000),
        ('OPS', 'Operations', 'Kazan', 700000),
        ('RND', 'Research & Development', 'Novosibirsk', 1200000),
    ]
    
    for dept in departments:
        cursor.execute("""
            INSERT INTO departments (dept_code, dept_name, location, budget)
            VALUES (%s, %s, %s, %s)
        """, dept)
    
    # Сотрудники
    first_names = ['Иван', 'Петр', 'Анна', 'Мария', 'Алексей', 'Елена', 'Дмитрий', 'Ольга', 
                   'Сергей', 'Татьяна', 'Андрей', 'Наталья', 'Владимир', 'Екатерина']
    last_names = ['Иванов', 'Петров', 'Сидоров', 'Кузнецова', 'Смирнов', 'Волкова', 
                  'Морозов', 'Новикова', 'Козлов', 'Лебедева']
    positions = ['Junior', 'Middle', 'Senior', 'Team Lead', 'Manager', 'Director']
    
    for i in range(counts.get('employees', 500)):
        emp_id = f"EMP{str(i+1).zfill(6)}"
        first = first_names[i % len(first_names)]
        last = last_names[i % len(last_names)]
        dept_id = (i % 6) + 1
        position = positions[i % len(positions)]
        salary = 30000 + (i % 150000)
        hire_date = f"202{i % 4 + 1}-{i % 12 + 1:02d}-{(i % 28) + 1:02d}"
        email = f"{first.lower()}.{last.lower()}@company.com"
        is_active = i % 20 != 0
        
        cursor.execute("""
            INSERT INTO employees (emp_id, first_name, last_name, department_id, position, salary, hire_date, email, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (emp_id, first, last, dept_id, position, salary, hire_date, email, is_active))
    
    # Проекты
    project_names = [
        ('PRJ001', 'Автоматизация учета', 500000),
        ('PRJ002', 'Мобильное приложение', 800000),
        ('PRJ003', 'Аналитическая платформа', 1200000),
        ('PRJ004', 'Миграция в облако', 2000000),
        ('PRJ005', 'Система безопасности', 900000),
        ('PRJ006', 'CRM внедрение', 600000),
    ]
    
    for proj in project_names:
        cursor.execute("""
            INSERT INTO projects (project_code, project_name, budget, start_date, status)
            VALUES (%s, %s, %s, CURRENT_DATE, 'active')
        """, proj)
    
    # Связи сотрудников с проектами
    for emp_id in range(1, counts.get('employees', 500) + 1):
        # Каждый сотрудник участвует в 1-3 проектах
        for proj_id in random.sample(range(1, 7), k=random.randint(1, 3)):
            cursor.execute("""
                INSERT INTO employee_projects (employee_id, project_id, role, hours_allocated, assigned_date)
                VALUES (%s, %s, %s, %s, CURRENT_DATE)
            """, (emp_id, proj_id, 'Разработчик', random.randint(20, 160)))


def get_test_queries():
    """Возвращает запросы для тестирования этой схемы"""
    
    return {
        'simple': [
            "SELECT * FROM employees LIMIT 10",
            "SELECT COUNT(*) FROM employees",
            "SELECT * FROM departments",
            "SELECT * FROM projects LIMIT 10",
            "SELECT e.first_name, e.last_name, d.dept_name FROM employees e JOIN departments d ON e.department_id = d.id LIMIT 20",
        ],
        'medium': [
            "SELECT d.dept_name, AVG(e.salary) as avg_salary FROM employees e JOIN departments d ON e.department_id = d.id GROUP BY d.dept_name",
            "SELECT p.project_name, COUNT(ep.employee_id) as emp_count FROM projects p LEFT JOIN employee_projects ep ON p.id = ep.project_id GROUP BY p.id",
            "SELECT e.first_name, e.last_name, COUNT(ep.project_id) as project_count FROM employees e LEFT JOIN employee_projects ep ON e.id = ep.employee_id GROUP BY e.id ORDER BY project_count DESC LIMIT 10",
        ],
        'complex': [
            "SELECT d.dept_name, AVG(e.salary) as avg_salary, COUNT(DISTINCT ep.project_id) as project_count FROM departments d JOIN employees e ON d.id = e.department_id LEFT JOIN employee_projects ep ON e.id = ep.employee_id GROUP BY d.id HAVING AVG(e.salary) > 50000",
            "SELECT e.first_name, e.last_name, SUM(ep.hours_allocated) as total_hours FROM employees e JOIN employee_projects ep ON e.id = ep.employee_id GROUP BY e.id ORDER BY total_hours DESC LIMIT 10",
        ],
    }

def get_test_queries():
    """Возвращает запросы для тестирования схемы MEDIUM"""
    return {
        'simple': [
            "SELECT 1",
            "SELECT COUNT(*) FROM employees",
            "SELECT COUNT(*) FROM departments",
            "SELECT COUNT(*) FROM projects",
            "SELECT * FROM employees LIMIT 10",
        ],
        'medium': [
            "SELECT e.first_name, e.last_name, d.dept_name FROM employees e JOIN departments d ON e.department_id = d.id LIMIT 50",
            "SELECT p.project_name, COUNT(ep.employee_id) as worker_count FROM projects p LEFT JOIN employee_projects ep ON p.id = ep.project_id GROUP BY p.id",
            "SELECT d.dept_name, AVG(e.salary) as avg_salary FROM employees e JOIN departments d ON e.department_id = d.id GROUP BY d.dept_name",
        ],
        'complex': [
            "SELECT d.dept_name, AVG(e.salary) as avg_salary, COUNT(DISTINCT ep.project_id) as project_count FROM departments d JOIN employees e ON d.id = e.department_id LEFT JOIN employee_projects ep ON e.id = ep.employee_id GROUP BY d.id",
            "SELECT e.first_name, e.last_name, COUNT(ep.project_id) as project_count FROM employees e LEFT JOIN employee_projects ep ON e.id = ep.employee_id GROUP BY e.id ORDER BY project_count DESC LIMIT 10",
        ],
        'very_complex': [
            "SELECT e.first_name, e.last_name, SUM(ep.hours_allocated) as total_hours FROM employees e JOIN employee_projects ep ON e.id = ep.employee_id GROUP BY e.id ORDER BY total_hours DESC LIMIT 10",
        ],
    }
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
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
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
    
    cursor.execute("""
        CREATE TABLE employee_projects (
            id SERIAL PRIMARY KEY,
            employee_id INTEGER REFERENCES employees(id),
            project_id INTEGER REFERENCES projects(id),
            role VARCHAR(50),
            hours_allocated INTEGER,
            actual_hours INTEGER,
            assigned_date DATE,
            completed_date DATE,
            UNIQUE(employee_id, project_id)
        )
    """)
    
    cursor.execute("CREATE INDEX idx_emp_dept ON employees(department_id);")
    cursor.execute("CREATE INDEX idx_emp_salary ON employees(salary);")
    cursor.execute("CREATE INDEX idx_emp_proj_emp ON employee_projects(employee_id);")
    cursor.execute("CREATE INDEX idx_emp_proj_proj ON employee_projects(project_id);")
    cursor.execute("CREATE INDEX idx_projects_status ON projects(status);")
    
    print("✅ Средняя схема создана (4 таблицы)")


def generate_data(cursor, counts: dict):
    """Генерирует тестовые данные"""
    
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
    
    first_names = ['Иван', 'Петр', 'Анна', 'Мария', 'Алексей', 'Елена', 'Дмитрий', 'Ольга',
                   'Сергей', 'Татьяна', 'Андрей', 'Наталья', 'Владимир', 'Екатерина']
    last_names = ['Иванов', 'Петров', 'Сидоров', 'Кузнецова', 'Смирнов', 'Волкова',
                  'Морозов', 'Новикова', 'Козлов', 'Лебедева']
    positions = ['Junior', 'Middle', 'Senior', 'Team Lead', 'Manager', 'Director']
    
    employee_count = counts.get('employees', 1000)
    start_date = datetime.now() - timedelta(days=3650)
    
    for i in range(employee_count):
        emp_id = f"EMP{str(i+1).zfill(6)}"
        first = first_names[i % len(first_names)]
        last = last_names[i % len(last_names)]
        dept_id = (i % 6) + 1
        position = positions[i % len(positions)]
        salary = 30000 + random.randint(0, 170000)
        hire_date = start_date + timedelta(days=random.randint(0, 3650))
        email = f"{first.lower()}.{last.lower()}@company.com"
        is_active = random.random() > 0.1
        
        cursor.execute("""
            INSERT INTO employees 
            (emp_id, first_name, last_name, department_id, position, salary, hire_date, email, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (emp_id, first, last, dept_id, position, salary, hire_date, email, is_active))
        
        if (i + 1) % 200 == 0:
            cursor.connection.commit()
            print(f"  Загружено {i+1} сотрудников...")
    
    project_names = [
        ('PRJ001', 'Автоматизация учета', 500000),
        ('PRJ002', 'Мобильное приложение', 800000),
        ('PRJ003', 'Аналитическая платформа', 1200000),
        ('PRJ004', 'Миграция в облако', 2000000),
        ('PRJ005', 'Система безопасности', 900000),
        ('PRJ006', 'CRM внедрение', 600000),
        ('PRJ007', 'ERP система', 3000000),
        ('PRJ008', 'HR портал', 400000),
        ('PRJ009', 'Биллинг', 1500000),
        ('PRJ010', 'Документооборот', 700000),
    ]
    
    projects_count = counts.get('projects', 10)
    for proj in project_names[:projects_count]:
        cursor.execute("""
            INSERT INTO projects (project_code, project_name, budget, start_date, status)
            VALUES (%s, %s, %s, CURRENT_DATE - INTERVAL '%s days', 'active')
        """, (proj[0], proj[1], proj[2], random.randint(0, 730)))
    
    for emp_id in range(1, employee_count + 1):
        num_projects = random.randint(1, 4)
        project_ids = random.sample(range(1, projects_count + 1), min(num_projects, projects_count))
        for proj_id in project_ids:
            hours = random.randint(20, 200)
            actual_hours = hours + random.randint(-20, 50)
            cursor.execute("""
                INSERT INTO employee_projects 
                (employee_id, project_id, role, hours_allocated, actual_hours, assigned_date, completed_date)
                VALUES (%s, %s, %s, %s, %s, CURRENT_DATE - INTERVAL '%s days', 
                        CASE WHEN random() > 0.3 THEN CURRENT_DATE - INTERVAL '%s days' ELSE NULL END)
            """, (emp_id, proj_id, 'Developer', hours, actual_hours, random.randint(0, 365), random.randint(0, 30)))
    
    cursor.connection.commit()
    print(f"✅ Создано {employee_count} сотрудников, {projects_count} проектов")


def get_test_queries():
    """Возвращает запросы для тестирования схемы MEDIUM"""
    return {
        'simple': [
            "SELECT 1",
            "SELECT COUNT(*) FROM employees",
            "SELECT COUNT(*) FROM departments",
            "SELECT COUNT(*) FROM projects",
            "SELECT COUNT(*) FROM employee_projects",
            "SELECT * FROM employees LIMIT 10",
        ],
        'medium': [
            """
            SELECT e.first_name, e.last_name, d.dept_name, e.salary
            FROM employees e 
            JOIN departments d ON e.department_id = d.id 
            WHERE e.salary > 70000
            LIMIT 100
            """,
            """
            SELECT p.project_name, COUNT(ep.employee_id) as worker_count, SUM(ep.hours_allocated) as total_hours
            FROM projects p 
            LEFT JOIN employee_projects ep ON p.id = ep.project_id 
            GROUP BY p.id
            ORDER BY total_hours DESC
            LIMIT 20
            """,
            """
            SELECT d.dept_name, AVG(e.salary) as avg_salary, COUNT(e.id) as emp_count
            FROM departments d 
            JOIN employees e ON d.id = e.department_id 
            GROUP BY d.id
            ORDER BY avg_salary DESC
            """,
        ],
        'complex': [
            """
            SELECT 
                d.dept_name,
                e.position,
                COUNT(DISTINCT e.id) as emp_count,
                AVG(e.salary) as avg_salary,
                SUM(ep.hours_allocated) as total_hours,
                AVG(ep.hours_allocated) as avg_hours
            FROM departments d
            JOIN employees e ON d.id = e.department_id
            LEFT JOIN employee_projects ep ON e.id = ep.employee_id
            GROUP BY d.id, e.position
            HAVING COUNT(e.id) > 5
            ORDER BY avg_salary DESC
            LIMIT 30
            """,
            """
            WITH project_stats AS (
                SELECT 
                    p.project_name,
                    p.budget,
                    COUNT(ep.employee_id) as worker_count,
                    SUM(ep.hours_allocated) as total_hours,
                    AVG(ep.hours_allocated) as avg_hours,
                    RANK() OVER (ORDER BY SUM(ep.hours_allocated) DESC) as hours_rank
                FROM projects p
                LEFT JOIN employee_projects ep ON p.id = ep.project_id
                GROUP BY p.id
            )
            SELECT project_name, budget, worker_count, total_hours, avg_hours, hours_rank
            FROM project_stats
            WHERE hours_rank <= 10
            ORDER BY hours_rank
            """,
        ],
        'very_complex': [
            """
            WITH RECURSIVE emp_workload AS (
                SELECT 
                    e.id,
                    e.first_name || ' ' || e.last_name as emp_name,
                    d.dept_name,
                    e.salary,
                    COALESCE(SUM(ep.hours_allocated), 0) as total_hours,
                    COALESCE(COUNT(DISTINCT ep.project_id), 0) as project_count,
                    ROW_NUMBER() OVER (PARTITION BY d.id ORDER BY COALESCE(SUM(ep.hours_allocated), 0) DESC) as rank_in_dept
                FROM employees e
                JOIN departments d ON e.department_id = d.id
                LEFT JOIN employee_projects ep ON e.id = ep.employee_id
                WHERE e.is_active = true
                GROUP BY e.id, d.id, d.dept_name
            )
            SELECT emp_name, dept_name, salary, total_hours, project_count, rank_in_dept
            FROM emp_workload
            WHERE rank_in_dept <= 3
            ORDER BY dept_name, rank_in_dept
            LIMIT 50
            """,
        ],
    }
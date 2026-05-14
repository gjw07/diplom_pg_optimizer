#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Модуль генетического алгоритма (Модуль 4 из Плана 2, Этап 3)
Реализует: создание популяции, операторы отбора, скрещивания и мутации.
Использует библиотеку DEAP.
"""

import random
import numpy as np
from deap import base, creator, tools
import logging
from typing import Dict, List, Tuple, Callable, Any
import copy

logger = logging.getLogger(__name__)


class GeneticAlgorithmEngine:
    """
    Класс, реализующий генетический алгоритм для оптимизации параметров БД.
    Соответствует модулю evolution_engine из архитектурного плана.
    """
    
    def __init__(self, params_config: Dict, ga_config: Dict, 
                 evaluate_func: Callable):
        """
        Инициализация движка генетического алгоритма.
        
        Args:
            params_config: Конфигурация оптимизируемых параметров
            ga_config: Конфигурация ГА (размер популяции, вероятности и т.д.)
            evaluate_func: Функция для оценки особи (фитнес-функция)
        """
        self.params_config = params_config
        self.ga_config = ga_config
        self.evaluate_func = evaluate_func
        
        # Создаем классы для DEAP
        creator.create("FitnessMax", base.Fitness, weights=(1.0,))
        creator.create("Individual", list, fitness=creator.FitnessMax)
        
        self.toolbox = base.Toolbox()
        self._setup_genetic_operators()
        
        self.generation_stats = []
        
        # ================================================================
        # ДОБАВЛЕНО: Хранение лучшей особи за всю историю
        # ================================================================
        self.best_ever_individual = None
        self.best_ever_fitness = -float('inf')
        self.best_ever_generation = -1
        
        logger.info("GeneticAlgorithmEngine инициализирован")
    
    def _create_individual(self) -> list:
        """
        Создает одну особь (индивидуума) - случайный набор параметров.
        
        Returns:
            list: Список значений генов
        """
        individual = []
        for param_name, param_info in self.params_config.items():
            if param_info['type'] == int:
                value = random.randint(param_info['min'], param_info['max'])
            else:  # float
                value = random.uniform(param_info['min'], param_info['max'])
                value = round(value, 2)
            individual.append(value)
        return individual
    
    def _setup_genetic_operators(self):
        """
        Настраивает генетические операторы в DEAP toolbox.
        """
        # Регистрируем функцию создания индивидуума
        self.toolbox.register("individual", 
                              tools.initIterate, 
                              creator.Individual, 
                              self._create_individual)
        
        # Регистрируем функцию создания популяции
        self.toolbox.register("population", 
                              tools.initRepeat, 
                              list, 
                              self.toolbox.individual)
        
        # Регистрируем функцию оценки
        self.toolbox.register("evaluate", self.evaluate_func)
        
        # Регистрируем оператор скрещивания (crossover)
        self.toolbox.register("mate", self._custom_crossover)
        
        # Регистрируем оператор мутации
        self.toolbox.register("mutate", self._custom_mutation)
        
        # Регистрируем оператор отбора (турнирный отбор)
        self.toolbox.register("select", 
                              tools.selTournament, 
                              tournsize=self.ga_config['TOURNSIZE'])
    
    def _update_best_ever(self, individual, generation: int):
        """
        Обновляет лучшую особь за всю историю, если текущая лучше.
        
        Args:
            individual: Особь для проверки
            generation: Текущее поколение
        """
        fitness_value = individual.fitness.values[0]
        if fitness_value > self.best_ever_fitness:
            self.best_ever_individual = individual
            self.best_ever_fitness = fitness_value
            self.best_ever_generation = generation
            logger.info(f"🎯 НОВАЯ ЛУЧШАЯ ОСОБЬ в поколении {generation}: fitness={fitness_value:.4f}")
    
    def _custom_crossover(self, ind1: list, ind2: list) -> Tuple[list, list]:
        """
        Кастомный оператор скрещивания (арифметический кроссовер).
        
        Args:
            ind1: Первый родитель
            ind2: Второй родитель
            
        Returns:
            Tuple[list, list]: Два потомка
        """
        if random.random() < self.ga_config['CXPB']:
            # Для каждой пары генов выполняем арифметический кроссовер
            alpha = random.uniform(0, 1)
            for i in range(len(ind1)):
                # Сохраняем значения до скрещивания
                v1, v2 = ind1[i], ind2[i]
                
                # Арифметический кроссовер
                ind1[i] = alpha * v1 + (1 - alpha) * v2
                ind2[i] = alpha * v2 + (1 - alpha) * v1
                
                # Проверяем границы значений
                param_name = list(self.params_config.keys())[i]
                param_info = self.params_config[param_name]
                
                ind1[i] = max(param_info['min'], min(param_info['max'], ind1[i]))
                ind2[i] = max(param_info['min'], min(param_info['max'], ind2[i]))
                
                # Округляем, если нужно
                if param_info['type'] == int:
                    ind1[i] = round(ind1[i])
                    ind2[i] = round(ind2[i])
                else:
                    ind1[i] = round(ind1[i], 2)
                    ind2[i] = round(ind2[i], 2)
        
        return ind1, ind2
    
    def _custom_mutation(self, individual: list, generation: int = None) -> Tuple[list]:
        """Кастомный оператор мутации с адаптивной силой"""
        if random.random() < self.ga_config['MUTPB']:
            # Адаптивная сила мутации: больше в начале, меньше в конце
            if generation is not None:
                max_gen = self.ga_config['GENERATIONS']
                mutation_strength = 0.3 * (1 - generation / max_gen) + 0.1
            else:
                mutation_strength = 0.2
            
            for i in range(len(individual)):
                if random.random() < 0.15:  # 15% генов мутируют
                    param_name = list(self.params_config.keys())[i]
                    param_info = self.params_config[param_name]
                    
                    sigma = (param_info['max'] - param_info['min']) * mutation_strength
                    mutation = random.gauss(0, sigma)
                    individual[i] += mutation
                    
                    # Проверяем границы
                    individual[i] = max(param_info['min'], 
                                       min(param_info['max'], individual[i]))
                    
                    # Округляем
                    if param_info['type'] == int:
                        individual[i] = round(individual[i])
                    else:
                        individual[i] = round(individual[i], 2)
        
        return (individual,)
    
    def individual_to_config(self, individual: list) -> Dict[str, Any]:
        """
        Преобразует индивидуума (список генов) в словарь конфигурации.
        
        Args:
            individual: Список значений генов
            
        Returns:
            Dict: Словарь с именами параметров и их значениями
        """
        config = {}
        for i, (param_name, param_info) in enumerate(self.params_config.items()):
            value = individual[i]
            config[param_name] = value
        return config
    
    def config_to_individual(self, config: Dict[str, Any]) -> list:
        """
        Преобразует словарь конфигурации в индивидуума.
        
        Args:
            config: Словарь с параметрами
            
        Returns:
            list: Список значений генов
        """
        individual = []
        for param_name in self.params_config.keys():
            individual.append(config[param_name])
        return individual
    
    def run_optimization(self, generations: int = None) -> Tuple[list, object]:
        """
        Запускает процесс оптимизации.
        
        Args:
            generations: Количество поколений (если None, берется из конфига)
            
        Returns:
            Tuple[list, object]: Лучший индивидуум за ВСЮ ИСТОРИЮ и лог статистики
        """
        if generations is None:
            generations = self.ga_config['GENERATIONS']
        
        # Создаем популяцию
        pop = self.toolbox.population(n=self.ga_config['POPULATION_SIZE'])
        
        # Настраиваем статистику
        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("avg", np.mean)
        stats.register("std", np.std)
        stats.register("min", np.min)
        stats.register("max", np.max)
        
        # Создаем лог
        logbook = tools.Logbook()
        logbook.header = ["gen", "evals"] + stats.fields
        
        # Оцениваем начальную популяцию
        fitnesses = list(map(self.toolbox.evaluate, pop))
        for ind, fit in zip(pop, fitnesses):
            ind.fitness.values = fit
        
        # ================================================================
        # ДОБАВЛЕНО: Обновляем лучшую особь после оценки начальной популяции
        # ================================================================
        for ind in pop:
            self._update_best_ever(ind, 0)
        
        # Собираем статистику
        record = stats.compile(pop)
        logbook.record(gen=0, evals=len(pop), **record)
        logger.info(f"Generation 0: {record}")
        
        # Основной цикл эволюции
        for gen in range(1, generations + 1):
            # Отбор
            offspring = self.toolbox.select(pop, len(pop))
            offspring = list(map(self.toolbox.clone, offspring))
            
            # Скрещивание и мутация
            for child1, child2 in zip(offspring[::2], offspring[1::2]):
                self.toolbox.mate(child1, child2)
                del child1.fitness.values
                del child2.fitness.values
            
            for mutant in offspring:
                self.toolbox.mutate(mutant)
                del mutant.fitness.values
            
            # Оценка новых особей
            invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
            fitnesses = map(self.toolbox.evaluate, invalid_ind)
            for ind, fit in zip(invalid_ind, fitnesses):
                ind.fitness.values = fit
            
            # Объединяем популяции (элитизм)
            combined = pop + offspring
            combined = sorted(combined, key=lambda x: x.fitness.values[0], reverse=True)
            pop = combined[:self.ga_config['POPULATION_SIZE']]
            
            # ================================================================
            # ДОБАВЛЕНО: Обновляем лучшую особь после каждого поколения
            # ================================================================
            for ind in pop:
                self._update_best_ever(ind, gen)
            
            # Собираем статистику
            record = stats.compile(pop)
            logbook.record(gen=gen, evals=len(invalid_ind), **record)
            logger.info(f"Generation {gen}: {record}")
            
            # Сохраняем статистику поколения
            self.generation_stats.append({
                'generation': gen,
                'avg_fitness': record['avg'],
                'max_fitness': record['max'],
                'min_fitness': record['min'],
                'std_fitness': record['std']
            })
        
        # ================================================================
        # ИСПРАВЛЕНО: Возвращаем лучшую особь за ВСЮ ИСТОРИЮ, а не из последнего поколения
        # ================================================================
        logger.info("=" * 60)
        logger.info(f"ОПТИМИЗАЦИЯ ЗАВЕРШЕНА")
        logger.info(f"Лучшая особь за всю историю:")
        logger.info(f"  Поколение: {self.best_ever_generation}")
        logger.info(f"  Fitness: {self.best_ever_fitness:.4f}")
        logger.info(f"  Конфигурация: {self.individual_to_config(self.best_ever_individual)}")
        logger.info("=" * 60)
        
        return self.best_ever_individual, logbook
    
    def get_best_ever_config(self) -> Dict[str, Any]:
        """
        Возвращает лучшую конфигурацию за всю историю.
        
        Returns:
            Dict: Лучшая конфигурация параметров
        """
        if self.best_ever_individual is None:
            return {}
        return self.individual_to_config(self.best_ever_individual)
    
    def get_best_ever_fitness_value(self) -> float:
        """
        Возвращает значение фитнеса лучшей особи за всю историю.
        
        Returns:
            float: Значение фитнеса
        """
        return self.best_ever_fitness
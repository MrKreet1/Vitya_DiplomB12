# B12 ORCA/OPI Pipeline

В этом репозитории я собрал Python-пайплайн для автоматизированного исследования кластера `B12` в `ORCA 6.1.1` с использованием `ORCA Python Interface (OPI)`.

Я делал этот проект как развитие предыдущей схемы для `B6`: сначала дешёвый screening стартовых геометрий, потом уточнение лучших кандидатов, проверка минимумов по частотам, high-level single-point расчёты и, при необходимости, более дорогие проверки `DLPNO-CCSD(T)` и `CASSCF/SC-NEVPT2`.

## Что я автоматизировал

В текущей версии пайплайн умеет:

- читать стартовые `*.xyz` из [`01_initial_structures/`](01_initial_structures/)
- строить ORCA-входы через `OPI`
- запускать расчёты по этапам в отдельных папках
- сохранять входные и выходные файлы каждого job
- извлекать из `*.out` итоговую энергию, нормальное завершение, `nimag`, `<S^2>`, `T1 diagnostic`, термохимию и другие ключевые параметры
- собирать `summary.csv` по каждому этапу
- формировать итоговые сводки для дипломной работы

## Логика расчётов

Я использую такой маршрут:

1. первичный screening стартовых структур на `r2SCAN-3c`
2. автоматический отбор низкоэнергетических кандидатов
3. уточнение геометрии лучших структур
4. проверка минимумов по частотам
5. high-level single-point на `PBE0-D4/def2-TZVPP`
6. контрольный `DLPNO-CCSD(T)/def2-TZVPP`
7. при необходимости `CASSCF` и `SC-NEVPT2`
8. сбор финальных таблиц и текстовых выводов

Этап `spin_comparison` я оставил в проекте как опциональный. По умолчанию он не входит в `full`.

## Структура репозитория

```text
b12_project/
├── 01_initial_structures/
├── 02_screening_r2scan3c/
├── 03_refined_candidates/
├── 04_frequencies/
├── 05_spin_comparison/
├── 06_highlevel_sp/
├── 07_dlpno_check/
├── 08_casscf_nevpt2/
├── config/
├── logs/
├── scripts/
├── src/b12_pipeline/
├── summaries/
└── tests/
```

## Конфигурация

Базовый конфиг лежит в [`config/b12_config.example.json`](config/b12_config.example.json).

Конфиг под мой профиль `Intel Core i5-14600KF` лежит в [`config/b12_config.i5_14600kf.json`](config/b12_config.i5_14600kf.json).

Основные параметры:

- `charge`
- `screening_multiplicities`
- `enable_spin_comparison`
- `spin_comparison_multiplicities`
- `resources.nprocs`
- `resources.maxcore_mb`
- `resources.stage_resources`
- `resources.orca_path`
- `resources.mpi_path`
- `selection.top_n`
- `selection.energy_window_kj_mol`
- `casscf.nel`
- `casscf.norb`

## Быстрый старт

Если я запускаю проект не из корня репозитория, сначала ставлю editable-режим:

```powershell
python -m pip install -e .
```

Из корня репозитория можно запускать и без установки:

```powershell
python -m b12_pipeline.cli full --config config/b12_config.example.json --dry-run
```

Для профиля `i5-14600KF`:

```powershell
python -m b12_pipeline.cli full --config config/b12_config.i5_14600kf.json --dry-run
```

## Как я запускаю этапы

Поэтапно:

```powershell
python scripts/run_screening.py --config config/b12_config.example.json
python scripts/select_candidates.py --config config/b12_config.example.json
python scripts/run_refinement.py --config config/b12_config.example.json
python scripts/run_frequencies.py --config config/b12_config.example.json
python scripts/run_highlevel_sp.py --config config/b12_config.example.json
python scripts/run_dlpno_check.py --config config/b12_config.example.json
python scripts/run_casscf_nevpt2.py --config config/b12_config.example.json
python scripts/build_final_reports.py --config config/b12_config.example.json
```

Полный прогон:

```powershell
python scripts/run_full_pipeline.py --config config/b12_config.example.json
```

Если мне всё же нужно принудительно сравнение мультиплетностей, я запускаю его отдельно:

```powershell
python scripts/run_spin_comparison.py --config config/b12_config.example.json
```

Если я хочу включить `spin_comparison` в `full`, я выставляю в конфиге:

```json
"enable_spin_comparison": true
```

## Где лежат результаты

Основные summary-файлы:

- [`02_screening_r2scan3c/summary.csv`](02_screening_r2scan3c/summary.csv)
- [`03_refined_candidates/selected_candidates.csv`](03_refined_candidates/selected_candidates.csv)
- [`03_refined_candidates/summary.csv`](03_refined_candidates/summary.csv)
- [`04_frequencies/summary.csv`](04_frequencies/summary.csv)
- [`05_spin_comparison/summary.csv`](05_spin_comparison/summary.csv)
- [`06_highlevel_sp/summary.csv`](06_highlevel_sp/summary.csv)
- [`07_dlpno_check/summary.csv`](07_dlpno_check/summary.csv)
- [`08_casscf_nevpt2/summary.csv`](08_casscf_nevpt2/summary.csv)
- [`summaries/final_method_comparison.csv`](summaries/final_method_comparison.csv)
- [`summaries/final_conclusion.txt`](summaries/final_conclusion.txt)

Полные выводы ORCA я смотрю в `*.out` внутри соответствующих этапов. Например:

- screening: [`02_screening_r2scan3c/b12_hexagonal_prism/mult_1/b12_hexagonal_prism_m1_screen.out`](02_screening_r2scan3c/b12_hexagonal_prism/mult_1/b12_hexagonal_prism_m1_screen.out)
- refinement: [`03_refined_candidates/b12_hexagonal_prism/mult_1/b12_hexagonal_prism_m1_refine.out`](03_refined_candidates/b12_hexagonal_prism/mult_1/b12_hexagonal_prism_m1_refine.out)
- frequencies: [`04_frequencies/b12_hexagonal_prism/mult_1/b12_hexagonal_prism_m1_freq.out`](04_frequencies/b12_hexagonal_prism/mult_1/b12_hexagonal_prism_m1_freq.out)
- high-level SP: [`06_highlevel_sp/b12_hexagonal_prism/mult_1/b12_hexagonal_prism_m1_highlevel.out`](06_highlevel_sp/b12_hexagonal_prism/mult_1/b12_hexagonal_prism_m1_highlevel.out)
- DLPNO: [`07_dlpno_check/b12_hexagonal_prism/mult_1/b12_hexagonal_prism_m1_dlpno.out`](07_dlpno_check/b12_hexagonal_prism/mult_1/b12_hexagonal_prism_m1_dlpno.out)
- CASSCF: [`08_casscf_nevpt2/b12_hexagonal_prism/mult_1/casscf/b12_hexagonal_prism_m1_casscf.out`](08_casscf_nevpt2/b12_hexagonal_prism/mult_1/casscf/b12_hexagonal_prism_m1_casscf.out)
- NEVPT2: [`08_casscf_nevpt2/b12_hexagonal_prism/mult_1/nevpt2/b12_hexagonal_prism_m1_nevpt2.out`](08_casscf_nevpt2/b12_hexagonal_prism/mult_1/nevpt2/b12_hexagonal_prism_m1_nevpt2.out)

## Подробный результат текущего прогона

Ниже я фиксирую фактический результат уже выполненного прогона для стартовой геометрии `b12_hexagonal_prism`.

### Screening на `r2SCAN-3c`

Источник: [`02_screening_r2scan3c/summary.csv`](02_screening_r2scan3c/summary.csv)

| Multiplicity | Energy, Eh | Relative energy, kJ/mol | Normal termination | Optimization converged |
| --- | ---: | ---: | --- | --- |
| 1 | -297.793921656920 | 0.0000 | True | False |
| 3 | -297.727313269881 | 174.8803 | True | False |
| 5 | -297.569949410132 | 588.0390 | True | False |

На screening singlet оказался самым низким по энергии уже на дешёвом уровне.

### Уточнение геометрии

Источник: [`03_refined_candidates/summary.csv`](03_refined_candidates/summary.csv)

| Structure | Multiplicity | Energy, Eh | Normal termination | Optimization converged |
| --- | ---: | ---: | --- | --- |
| b12_hexagonal_prism | 1 | -297.794408679592 | True | True |

Оптимизированная геометрия сохранена в [`03_refined_candidates/b12_hexagonal_prism/mult_1/b12_hexagonal_prism_m1_refine_saved.xyz`](03_refined_candidates/b12_hexagonal_prism/mult_1/b12_hexagonal_prism_m1_refine_saved.xyz).

### Частотный анализ

Источник: [`04_frequencies/summary.csv`](04_frequencies/summary.csv)

| Multiplicity | Energy, Eh | nimag | Min freq, cm-1 | Max freq, cm-1 | ZPE, Eh | Gibbs free energy, Eh |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | -297.794408679930 | 0 | 0.00 | 1325.78 | 0.04930687 | -297.77613518 |

Для текущей оптимизированной структуры я получил `nimag = 0`, то есть локальный минимум на поверхности потенциальной энергии подтверждён.

### Опциональный spin comparison

Этап не обязателен и по умолчанию не входит в `full`, но я один раз запускал его как тест.

Источник: [`05_spin_comparison/summary.csv`](05_spin_comparison/summary.csv)

| Multiplicity | SP energy, Eh | Relative energy, kJ/mol | nimag | <S^2> |
| --- | ---: | ---: | ---: | ---: |
| 1 | -297.606945704388 | 0.0000 | 0 |  |
| 3 | -297.587246435772 | 51.7204 | 0 | 2.036319 |
| 5 | -297.534632840554 | 189.8574 | 0 | 6.054539 |

В этом тестовом сравнении singlet оказался ниже triplet и quintet.

### High-level single-point и дорогие проверки

| Method | Multiplicity | Energy, Eh | Normal termination | Source |
| --- | ---: | ---: | --- | --- |
| PBE0-D4/def2-TZVPP | 1 | -297.606944496257 | True | [`06_highlevel_sp/summary.csv`](06_highlevel_sp/summary.csv) |
| DLPNO-CCSD(T)/def2-TZVPP | 1 | -297.135984193233 | True | [`07_dlpno_check/summary.csv`](07_dlpno_check/summary.csv) |
| CASSCF | 1 | -295.928927541449 | True | [`08_casscf_nevpt2/summary.csv`](08_casscf_nevpt2/summary.csv) |
| SC-NEVPT2 | 1 | -297.050127607406 | True | [`08_casscf_nevpt2/summary.csv`](08_casscf_nevpt2/summary.csv) |

Первый запуск `DLPNO-CCSD(T)` у меня падал по памяти на triples. После уменьшения ресурсов этапа до `8` процессов и `2500 MB` на процесс расчёт завершился нормально.

## Что я могу утверждать по текущему результату

По состоянию на этот прогон я могу утверждать следующее:

- для протестированной геометрии `b12_hexagonal_prism` найден устойчивый singlet-минимум
- оптимизация геометрии действительно проводилась от заданных начальных координат
- минимум подтверждён частотным анализом, потому что `nimag = 0`
- high-level, `DLPNO-CCSD(T)` и `SC-NEVPT2` успешно отработали и дали контрольные энергии

При этом я не считаю, что этим прогоном уже доказан глобальный минимум всего `B12`, потому что:

- пока использована только одна стартовая геометрия
- сравнение разных изомеров между собой ещё не завершено
- дорогие методы запускались только для лучшего найденного кандидата

## Как я проверяю статус расчётов

Проверить, идёт ли сейчас ORCA:

```powershell
Get-Process | Where-Object { $_.ProcessName -match 'orca|mpirun|orterun' }
```

Посмотреть журнал стартов и завершений:

```powershell
Get-Content .\logs\pipeline_events.log -Tail 30 -Wait
```

Проверить, завершился ли конкретный расчёт нормально:

```powershell
Select-String -Path .\07_dlpno_check\b12_hexagonal_prism\mult_1\b12_hexagonal_prism_m1_dlpno.out -Pattern "ORCA TERMINATED NORMALLY"
```

Если я перезапускаю только один этап, потом заново собираю итоговые сводки:

```powershell
python -m b12_pipeline.cli finalize --config config/b12_config.i5_14600kf.json
```

## Ответ на частый вопрос

### Проводилось ли здесь задание начальных координат с последующим поиском оптимальной геометрии и минимальной энергии?

Да.

Я задал начальные координаты в файле [`01_initial_structures/b12_hexagonal_prism.xyz`](01_initial_structures/b12_hexagonal_prism.xyz), после чего ORCA выполнила итерационную оптимизацию геометрии. Оптимизированная структура была сохранена в [`03_refined_candidates/b12_hexagonal_prism/mult_1/b12_hexagonal_prism_m1_refine_saved.xyz`](03_refined_candidates/b12_hexagonal_prism/mult_1/b12_hexagonal_prism_m1_refine_saved.xyz), а её энергия записана в [`03_refined_candidates/summary.csv`](03_refined_candidates/summary.csv) и равна `-297.794408679592 Eh`.

Это означает, что для данной стартовой геометрии я нашёл локальный минимум. Это подтверждается частотным анализом, потому что в [`04_frequencies/summary.csv`](04_frequencies/summary.csv) указано `nimag = 0`.

## Ограничения

- Активное пространство для `CASSCF/SC-NEVPT2` я задаю через конфиг, и под реальные состояния `B12` его может понадобиться дополнительно калибровать.
- Парсинг частот, occupation numbers и части диагностик идёт из текстового ORCA-выхода, поэтому при нестандартном формате `.out` summary-файлы стоит дополнительно проверить вручную.
- При `--dry-run` я только генерирую входные файлы ORCA, но не запускаю вычисления.
- Для реального запуска пути к `ORCA` и при необходимости `MPI` должны быть корректно заданы в конфиге.

## Рекомендации по ресурсам для `i5-14600KF`

Для своего процессора я использую профиль [`config/b12_config.i5_14600kf.json`](config/b12_config.i5_14600kf.json) со следующими настройками:

- `screening/refinement/frequencies/spin_opt/spin_freq`: `8` процессов
- `spin_sp/highlevel_sp`: `10` процессов
- `dlpno_check`: `8` процессов и `2500 MB` на процесс
- `casscf/nevpt2`: `6` процессов

Если памяти меньше `32 GB`, я бы дополнительно снижал `maxcore_mb`.

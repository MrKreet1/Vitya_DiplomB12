# B12 ORCA/OPI Pipeline

Python-проект для автоматизированного исследования кластера `B12` в ORCA `6.1.1` с использованием `ORCA Python Interface (OPI)`.

Проект повторяет исследовательскую логику, уже использованную для `B6`:

1. первичный скрининг стартовых геометрий;
2. автоматический отбор низкоэнергетических кандидатов;
3. уточнение геометрии;
4. проверка минимумов по частотам;
5. маршрут `OPT + FREQ + SP` для сравнения спиновых состояний;
6. high-level single-point расчёты;
7. контрольные `DLPNO-CCSD(T)`;
8. `CASSCF / SC-NEVPT2` при наличии диагностических оснований;
9. сбор сводных таблиц и текстовых отчётов для диплома.

## Структура

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

## Что делает пайплайн

- читает все `*.xyz` из [01_initial_structures](/c:/Users/gnome/Desktop/Vitya_Diplom/Vitya_DiplomB12/01_initial_structures);
- строит и запускает входы ORCA через `OPI`;
- раскладывает расчёты по этапам и подпапкам `structure_name/mult_X`;
- извлекает ключевые величины из `*.out` через regex-парсинг:
  итоговую энергию, нормальное завершение, `<S^2>`, `T1 diagnostic`, `nimag`, диапазон частот, термохимию, occupation numbers;
- формирует `summary.csv` по каждому этапу;
- создаёт итоговые файлы в [summaries](/c:/Users/gnome/Desktop/Vitya_Diplom/Vitya_DiplomB12/summaries).

## Конфигурация

Базовый конфиг лежит в [config/b12_config.example.json](/c:/Users/gnome/Desktop/Vitya_Diplom/Vitya_DiplomB12/config/b12_config.example.json).

Основные параметры:

- `charge`
- `screening_multiplicities`
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

## Запуск

Установка editable-режима:

```powershell
python -m pip install -e .
```

Из корня репозитория команды `python -m b12_pipeline.cli ...` тоже работают напрямую, потому что в проект добавлен корневой shim-пакет [b12_pipeline/__init__.py](/c:/Users/gnome/Desktop/Vitya_Diplom/Vitya_DiplomB12/b12_pipeline/__init__.py), расширяющий путь до `src/b12_pipeline`. Если запуск идёт не из корня проекта, используйте `python -m pip install -e .`.

Сухой прогон без запуска ORCA:

```powershell
python -m b12_pipeline.cli full --config config/b12_config.example.json --dry-run
```

Профиль под `Intel Core i5-14600KF`:

```powershell
python -m b12_pipeline.cli full --config config/b12_config.i5_14600kf.json --dry-run
```

Поэтапный запуск:

```powershell
python scripts/run_screening.py --config config/b12_config.example.json
python scripts/select_candidates.py --config config/b12_config.example.json
python scripts/run_refinement.py --config config/b12_config.example.json
python scripts/run_frequencies.py --config config/b12_config.example.json
python scripts/run_spin_comparison.py --config config/b12_config.example.json
python scripts/run_highlevel_sp.py --config config/b12_config.example.json
python scripts/run_dlpno_check.py --config config/b12_config.example.json
python scripts/run_casscf_nevpt2.py --config config/b12_config.example.json
python scripts/build_final_reports.py --config config/b12_config.example.json
```

Полный прогон:

```powershell
python scripts/run_full_pipeline.py --config config/b12_config.example.json
```

## Основные выходные файлы

- [02_screening_r2scan3c/summary.csv](/c:/Users/gnome/Desktop/Vitya_Diplom/Vitya_DiplomB12/02_screening_r2scan3c/summary.csv)
- [03_refined_candidates/selected_candidates.csv](/c:/Users/gnome/Desktop/Vitya_Diplom/Vitya_DiplomB12/03_refined_candidates/selected_candidates.csv)
- [03_refined_candidates/summary.csv](/c:/Users/gnome/Desktop/Vitya_Diplom/Vitya_DiplomB12/03_refined_candidates/summary.csv)
- [04_frequencies/summary.csv](/c:/Users/gnome/Desktop/Vitya_Diplom/Vitya_DiplomB12/04_frequencies/summary.csv)
- [05_spin_comparison/summary.csv](/c:/Users/gnome/Desktop/Vitya_Diplom/Vitya_DiplomB12/05_spin_comparison/summary.csv)
- [06_highlevel_sp/summary.csv](/c:/Users/gnome/Desktop/Vitya_Diplom/Vitya_DiplomB12/06_highlevel_sp/summary.csv)
- [07_dlpno_check/summary.csv](/c:/Users/gnome/Desktop/Vitya_Diplom/Vitya_DiplomB12/07_dlpno_check/summary.csv)
- [08_casscf_nevpt2/summary.csv](/c:/Users/gnome/Desktop/Vitya_Diplom/Vitya_DiplomB12/08_casscf_nevpt2/summary.csv)
- [summaries/final_method_comparison.csv](/c:/Users/gnome/Desktop/Vitya_Diplom/Vitya_DiplomB12/summaries/final_method_comparison.csv)
- [summaries/final_conclusion.txt](/c:/Users/gnome/Desktop/Vitya_Diplom/Vitya_DiplomB12/summaries/final_conclusion.txt)

## Подробный отчёт по результатам

Ниже приведён отчёт по фактически выполненному прогону для стартовой геометрии `b12_hexagonal_prism`. После повторного запуска `DLPNO-CCSD(T)` этап завершился нормально, а итоговые файлы были пересобраны командой `finalize`.

### 1. Что именно было рассчитано

- стартовая структура: `B12` в геометрии `hexagonal prism`
- заряд: `0`
- screening-мультиплетности: `1`, `3`, `5`
- базовый уровень: `r2SCAN-3c`
- high-level single-point: `PBE0-D4/def2-TZVPP`
- correlated check: `DLPNO-CCSD(T)/def2-TZVPP`
- multireference check: `CASSCF` и `SC-NEVPT2`

### 2. Первичный screening на r2SCAN-3c

Результаты этапа [02_screening_r2scan3c/summary.csv](/c:/Users/gnome/Desktop/Vitya_Diplom/Vitya_DiplomB12/02_screening_r2scan3c/summary.csv):

| Multiplicity | Energy, Eh | Relative energy, kJ/mol | Normal termination | Optimization converged |
| --- | ---: | ---: | --- | --- |
| 1 | -297.793921656920 | 0.0000 | True | False |
| 3 | -297.727313269881 | 174.8803 | True | False |
| 5 | -297.569949410132 | 588.0390 | True | False |

Вывод по screening:

- уже на дешёвом этапе singlet оказался существенно ниже triplet и quintet;
- screening использовался как быстрый этап отбора, поэтому отсутствие полного `optimization_converged` в этих задачах не мешало переходу к уточнению лучшего кандидата.

### 3. Уточнение геометрии и частоты

Результаты уточнения геометрии: [03_refined_candidates/summary.csv](/c:/Users/gnome/Desktop/Vitya_Diplom/Vitya_DiplomB12/03_refined_candidates/summary.csv)

| Structure | Multiplicity | Energy, Eh | Normal termination | Optimization converged |
| --- | ---: | ---: | --- | --- |
| b12_hexagonal_prism | 1 | -297.794408679592 | True | True |

Результаты частотного анализа: [04_frequencies/summary.csv](/c:/Users/gnome/Desktop/Vitya_Diplom/Vitya_DiplomB12/04_frequencies/summary.csv)

| Multiplicity | Energy, Eh | nimag | Min freq, cm-1 | Max freq, cm-1 | ZPE, Eh | Gibbs free energy, Eh |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | -297.794408679930 | 0 | 0.00 | 1325.78 | 0.04930687 | -297.77613518 |

Вывод по геометрии и частотам:

- структура `b12_hexagonal_prism` в singlet-состоянии подтверждена как минимум на поверхности потенциальной энергии;
- мнимых частот не обнаружено (`nimag = 0`);
- refined geometry была использована дальше во всех более дорогих расчётах.

### 4. Сравнение спиновых состояний

Результаты маршрута `OPT + FREQ + SP` на уровне `r2SCAN-3c / r2SCAN-3c / PBE0-D4/def2-TZVPP`:
[05_spin_comparison/summary.csv](/c:/Users/gnome/Desktop/Vitya_Diplom/Vitya_DiplomB12/05_spin_comparison/summary.csv)

| Multiplicity | SP energy, Eh | Relative energy, kJ/mol | nimag | <S^2> |
| --- | ---: | ---: | ---: | ---: |
| 1 | -297.606945704388 | 0.0000 | 0 |  |
| 3 | -297.587246435772 | 51.7204 | 0 | 2.036319 |
| 5 | -297.534632840554 | 189.8574 | 0 | 6.054539 |

Вывод по спиновым состояниям:

- singlet является самым низким по энергии состоянием для протестированной геометрии;
- triplet выше на `51.7204 kJ/mol`;
- quintet выше на `189.8574 kJ/mol`;
- для triplet и quintet значения `<S^2>` близки к ожидаемым, критичной spin contamination в этих данных не видно.

### 5. High-level single-point, DLPNO и NEVPT2

Результаты одноточечных и контрольных расчётов:

| Method | Multiplicity | Energy, Eh | Normal termination | Source |
| --- | ---: | ---: | --- | --- |
| PBE0-D4/def2-TZVPP | 1 | -297.606944496257 | True | [06_highlevel_sp/summary.csv](/c:/Users/gnome/Desktop/Vitya_Diplom/Vitya_DiplomB12/06_highlevel_sp/summary.csv) |
| DLPNO-CCSD(T)/def2-TZVPP | 1 | -297.135984193233 | True | [07_dlpno_check/summary.csv](/c:/Users/gnome/Desktop/Vitya_Diplom/Vitya_DiplomB12/07_dlpno_check/summary.csv) |
| CASSCF | 1 | -295.928927541449 | True | [08_casscf_nevpt2/summary.csv](/c:/Users/gnome/Desktop/Vitya_Diplom/Vitya_DiplomB12/08_casscf_nevpt2/summary.csv) |
| SC-NEVPT2 | 1 | -297.050127607406 | True | [08_casscf_nevpt2/summary.csv](/c:/Users/gnome/Desktop/Vitya_Diplom/Vitya_DiplomB12/08_casscf_nevpt2/summary.csv) |

Дополнительные замечания по дорогим этапам:

- первый запуск `DLPNO-CCSD(T)` падал из-за нехватки памяти на triples;
- после снижения ресурсов этапа `dlpno_check` до `8` процессов и `2500 MB` на процесс расчёт завершился нормально;
- итоговый `DLPNO`-вывод находится в [b12_hexagonal_prism_m1_dlpno.out](/c:/Users/gnome/Desktop/Vitya_Diplom/Vitya_DiplomB12/07_dlpno_check/b12_hexagonal_prism/mult_1/b12_hexagonal_prism_m1_dlpno.out);
- `CASSCF` и `SC-NEVPT2` тоже завершились нормально, их выводы находятся в [b12_hexagonal_prism_m1_casscf.out](/c:/Users/gnome/Desktop/Vitya_Diplom/Vitya_DiplomB12/08_casscf_nevpt2/b12_hexagonal_prism/mult_1/casscf/b12_hexagonal_prism_m1_casscf.out) и [b12_hexagonal_prism_m1_nevpt2.out](/c:/Users/gnome/Desktop/Vitya_Diplom/Vitya_DiplomB12/08_casscf_nevpt2/b12_hexagonal_prism/mult_1/nevpt2/b12_hexagonal_prism_m1_nevpt2.out).

### 6. Итоговый научный вывод по текущему прогону

Для протестированной структуры `b12_hexagonal_prism` текущий прогон даёт следующие выводы:

- наиболее вероятное основное состояние: `singlet`;
- singlet устойчиво ниже triplet и quintet в рамках выполненного spin-comparison;
- singlet-геометрия подтверждена как минимум по данным частотного анализа;
- high-level, DLPNO и multireference-этапы успешно выполнены и дают воспроизводимый набор контрольных энергий;
- проект в текущем состоянии уже формирует полноценные summary-файлы и пригоден для подготовки материалов дипломной работы.

### 7. Ограничения интерпретации

Этот прогон ещё не доказывает глобальный минимум для всего `B12`, потому что:

- в screening использовалась только одна стартовая геометрия;
- дорогие методы запускались только для лучшего найденного singlet-кандидата;
- сравнение isomer-to-isomer пока не выполнено, поэтому вывод о наиболее устойчивой геометрии относится только к протестированной призматической структуре.

Чтобы сделать итоговый вывод именно о глобальном минимуме `B12`, нужно добавить несколько альтернативных стартовых `*.xyz` и повторить screening-маршрут.

Актуальные итоговые сводки:

- [summaries/final_method_comparison.csv](/c:/Users/gnome/Desktop/Vitya_Diplom/Vitya_DiplomB12/summaries/final_method_comparison.csv)
- [summaries/final_conclusion.txt](/c:/Users/gnome/Desktop/Vitya_Diplom/Vitya_DiplomB12/summaries/final_conclusion.txt)

Если перезапускается только один этап, после него нужно заново собрать финальные сводки:

```powershell
python -m b12_pipeline.cli finalize --config config/b12_config.i5_14600kf.json
```

## Как проверять статус

Проверить, идёт ли сейчас ORCA:

```powershell
Get-Process | Where-Object { $_.ProcessName -match 'orca|mpirun|orterun' }
```

Посмотреть журнал этапов и старт/финиш задач:

```powershell
Get-Content .\logs\pipeline_events.log -Tail 30 -Wait
```

Проверить, завершился ли конкретный расчёт нормально:

```powershell
Select-String -Path .\07_dlpno_check\b12_hexagonal_prism\mult_1\b12_hexagonal_prism_m1_dlpno.out -Pattern "ORCA TERMINATED NORMALLY"
```

## Ограничения и замечания

- Для `CASSCF/SC-NEVPT2` активное пространство задаётся в конфиге и почти наверняка потребует ручной калибровки под реальные B12-состояния.
- Частотный парсинг и occupation numbers извлекаются из текстового ORCA-выхода, поэтому при редких форматных отличиях ORCA стоит проверить summary-файлы вручную.
- При `--dry-run` генерируются входные файлы ORCA, но вычисления не запускаются.
- Для реального запуска нужно, чтобы `ORCA` и при необходимости `MPI` были корректно доступны по путям из конфига.

## Рекомендации по i5-14600KF

Для `Intel Core i5-14600KF` в проекте добавлен профиль [config/b12_config.i5_14600kf.json](/c:/Users/gnome/Desktop/Vitya_Diplom/Vitya_DiplomB12/config/b12_config.i5_14600kf.json). В нём ресурсы разделены по этапам:

- `screening/refinement/frequencies/spin_opt/spin_freq`: `8` процессов, потому что для маленького `B12`-кластера DFT-оптимизации обычно плохо масштабируются выше этого.
- `spin_sp/highlevel_sp`: `10` процессов, чтобы ускорить single-point DFT без лишнего штрафа от слабого масштабирования.
- `dlpno_check`: `8` процессов и `2500 MB` на процесс, чтобы не упираться в память на triples при `32 GB RAM`.
- `casscf/nevpt2`: `6` процессов, чтобы не раздувать накладные расходы и требования к памяти.

Если у вас `16 GB RAM`, дополнительно уменьшите `maxcore_mb` примерно на `20-30%`. Если `32 GB RAM` и больше, текущий профиль обычно является хорошей безопасной стартовой точкой.

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

## Итог последнего прогона

Примерный полный прогон на `b12_hexagonal_prism` завершён. После повторного запуска `DLPNO-CCSD(T)` и повторного `finalize` итоговые файлы обновлены.

- `screening`: `-297.793921656920 Eh`
- `refinement`: `-297.794408679592 Eh`
- `frequencies`: `nimag = 0`, минимум подтверждён
- `spin_comparison`: singlet ниже triplet на `51.7204 kJ/mol` и ниже quintet на `189.8574 kJ/mol`
- `highlevel_sp`: `-297.606944496257 Eh`
- `dlpno_check`: `-297.135984193233 Eh`, `ORCA TERMINATED NORMALLY`
- `casscf_nevpt2`: `-297.050127607406 Eh`, `ORCA TERMINATED NORMALLY`

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

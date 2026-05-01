"""
База знаний для RAG.
Каждый документ — конкретный, actionable совет или набор ключевых слов.
Метаданные: grade (Junior/Middle/Senior/Lead/any), direction (Backend/Frontend/ML/..../any), doc_type.
"""

DOCUMENTS: list[dict] = [

    # ──────────────────────────────────────────────────────────────────────────
    # GRADE PATTERNS — как описывать опыт на каждом уровне
    # ──────────────────────────────────────────────────────────────────────────

    {
        "id": "grade_junior_01",
        "text": "Junior резюме: акцент на pet-проектах и учебных работах. "
                "Фраза-паттерн: 'Разработал телеграм-бота для X, используя Python и aiogram, "
                "задеплоил на VPS через Docker'. Конкретная технология + конкретный результат — "
                "даже если проект учебный. Не писать 'изучал Python' — писать 'реализовал'.",
        "grade": "Junior", "direction": "any", "doc_type": "patterns",
    },
    {
        "id": "grade_junior_02",
        "text": "Junior summary шаблон: 'Python-разработчик с X месяцами коммерческого опыта / "
                "опытом pet-проектов. Уверенно работаю с [стек]. Активно развиваюсь в направлении [X]. "
                "Ищу команду где смогу расти и приносить пользу с первых недель.' "
                "Энергия + конкретика стека + честность об уровне.",
        "grade": "Junior", "direction": "any", "doc_type": "patterns",
    },
    {
        "id": "grade_junior_03",
        "text": "Junior: что НЕ писать. Избегать: 'знаком с', 'имею представление о', "
                "'изучал курс'. Вместо этого: 'реализовал', 'разработал', 'настроил', 'написал тесты для'. "
                "Даже небольшое конкретное действие лучше расплывчатого знания.",
        "grade": "Junior", "direction": "any", "doc_type": "advice",
    },
    {
        "id": "grade_middle_01",
        "text": "Middle резюме: обязательны числовые метрики достижений. "
                "Паттерны: 'Оптимизировал SQL-запрос, снизив время ответа с 2с до 180мс', "
                "'Покрыл тестами 85% критического модуля', "
                "'Рефакторил legacy-код, сократив количество багов на 40% за квартал'. "
                "Каждый пункт опыта должен иметь измеримый результат.",
        "grade": "Middle", "direction": "any", "doc_type": "patterns",
    },
    {
        "id": "grade_middle_02",
        "text": "Middle: показывать самостоятельность. "
                "Фразы: 'Самостоятельно спроектировал и реализовал модуль X', "
                "'Декомпозировал задачу и выполнил без надзора за N спринтов', "
                "'Провёл code review 50+ PR за квартал'. "
                "HR ищет признаки что человек не требует постоянного контроля.",
        "grade": "Middle", "direction": "any", "doc_type": "patterns",
    },
    {
        "id": "grade_middle_03",
        "text": "Middle summary шаблон: 'Backend-разработчик с X летами коммерческого опыта. "
                "Специализируюсь на [стек]. Самостоятельно веду задачи от постановки до продакшена. "
                "Опыт работы в [тип команды/компании]. Фокус на качество кода и измеримые результаты.'",
        "grade": "Middle", "direction": "any", "doc_type": "patterns",
    },
    {
        "id": "grade_senior_01",
        "text": "Senior резюме: архитектурные решения и их последствия. "
                "Паттерны: 'Принял решение о переходе с монолита на микросервисы, "
                "что позволило масштабировать команду с 3 до 8 разработчиков', "
                "'Выбрал и внедрил PostgreSQL + Redis вместо MongoDB, снизив p99 latency на 60%', "
                "'Разработал архитектуру event-driven системы обработки 50k событий/сек'.",
        "grade": "Senior", "direction": "any", "doc_type": "patterns",
    },
    {
        "id": "grade_senior_02",
        "text": "Senior: влияние на команду и процессы. "
                "Фразы: 'Ввёл практику code review, снизив количество продакшен-багов на 35%', "
                "'Менторил 2 junior-разработчиков, оба выросли до middle за 8 месяцев', "
                "'Написал внутреннюю документацию и онбординг-гайд, сократив время онбординга с 2 недель до 3 дней'.",
        "grade": "Senior", "direction": "any", "doc_type": "patterns",
    },
    {
        "id": "grade_senior_03",
        "text": "Senior summary шаблон: 'Senior [направление]-разработчик с X+ летами опыта. "
                "Проектирую высоконагруженные системы, принимаю архитектурные решения. "
                "Опыт менторства и code review. Работал в [контекст: стартап/корпорация/аутсорс]. "
                "Специализация: [конкретная область — NLP, распределённые системы, etc.]'",
        "grade": "Senior", "direction": "any", "doc_type": "patterns",
    },
    {
        "id": "grade_lead_01",
        "text": "Lead резюме: управление командой с конкретными цифрами. "
                "Паттерны: 'Управлял командой из 6 backend-разработчиков', "
                "'Выстроил процесс найма: провёл 40+ интервью, нанял 3 senior-инженеров за квартал', "
                "'Внедрил Scrum, увеличив velocity команды на 25% за 2 спринта'.",
        "grade": "Lead", "direction": "any", "doc_type": "patterns",
    },
    {
        "id": "grade_lead_02",
        "text": "Lead: бизнес-метрики и стратегический уровень. "
                "Фразы: 'Сократил time-to-market новых фич с 3 недель до 5 дней через CI/CD', "
                "'Снизил MTTR с 4 часов до 20 минут через внедрение on-call rotation и runbooks', "
                "'Технически обосновал миграцию на облако, что сэкономило $120k/год на инфраструктуре'.",
        "grade": "Lead", "direction": "any", "doc_type": "patterns",
    },

    # ──────────────────────────────────────────────────────────────────────────
    # BACKEND KEYWORDS И ПАТТЕРНЫ
    # ──────────────────────────────────────────────────────────────────────────

    {
        "id": "dir_backend_keywords_python",
        "text": "Backend Python ATS-ключевые слова: Python, FastAPI, Django, Flask, asyncio, "
                "aiohttp, Celery, SQLAlchemy, Alembic, Pydantic, pytest, mypy, "
                "Poetry, pip, virtualenv, type hints, dataclasses.",
        "grade": "any", "direction": "Backend", "doc_type": "keywords",
    },
    {
        "id": "dir_backend_keywords_infra",
        "text": "Backend инфраструктурные ATS-ключевые слова: PostgreSQL, MySQL, Redis, MongoDB, "
                "Elasticsearch, Kafka, RabbitMQ, Docker, Docker Compose, Kubernetes, k8s, "
                "REST API, gRPC, GraphQL, OpenAPI, Swagger, nginx, gunicorn, uvicorn.",
        "grade": "any", "direction": "Backend", "doc_type": "keywords",
    },
    {
        "id": "dir_backend_achievements",
        "text": "Backend достижения-паттерны: "
                "'Оптимизировал N SQL-запросов, снизив нагрузку на БД на X%', "
                "'Спроектировал REST API для N эндпоинтов с документацией OpenAPI', "
                "'Реализовал асинхронную обработку очереди X задач/сек через Celery+Redis', "
                "'Настроил горизонтальное масштабирование сервиса до N инстансов в k8s'.",
        "grade": "any", "direction": "Backend", "doc_type": "achievements",
    },
    {
        "id": "dir_backend_highload",
        "text": "Backend высокие нагрузки — ключевые слова и паттерны: "
                "RPS (requests per second), p99 latency, throughput, connection pooling, "
                "caching strategy, database sharding, read replica, circuit breaker, "
                "rate limiting, backpressure, graceful degradation, bulkhead pattern.",
        "grade": "Senior", "direction": "Backend", "doc_type": "keywords",
    },

    # ──────────────────────────────────────────────────────────────────────────
    # FRONTEND KEYWORDS И ПАТТЕРНЫ
    # ──────────────────────────────────────────────────────────────────────────

    {
        "id": "dir_frontend_keywords_core",
        "text": "Frontend core ATS-ключевые слова: JavaScript, TypeScript, React, Vue.js, Angular, "
                "Next.js, Nuxt.js, HTML5, CSS3, SCSS/SASS, Tailwind CSS, styled-components, "
                "Webpack, Vite, Babel, ESLint, Prettier.",
        "grade": "any", "direction": "Frontend", "doc_type": "keywords",
    },
    {
        "id": "dir_frontend_keywords_perf",
        "text": "Frontend производительность ATS-ключевые слова: "
                "Core Web Vitals, LCP, FID, CLS, INP, Lighthouse, lazy loading, "
                "code splitting, tree shaking, SSR, SSG, ISR, hydration, "
                "bundle size optimization, performance budget.",
        "grade": "any", "direction": "Frontend", "doc_type": "keywords",
    },
    {
        "id": "dir_frontend_achievements",
        "text": "Frontend достижения-паттерны: "
                "'Улучшил LCP с 4.2с до 1.8с через lazy loading и оптимизацию изображений', "
                "'Сократил bundle size на 40% через code splitting и tree shaking', "
                "'Реализовал дизайн-систему из 30+ компонентов, ускорив разработку фич на 25%', "
                "'Перевёл проект с CRA на Vite, сократив время сборки с 90с до 8с'.",
        "grade": "any", "direction": "Frontend", "doc_type": "achievements",
    },

    # ──────────────────────────────────────────────────────────────────────────
    # ML / DATA SCIENCE KEYWORDS И ПАТТЕРНЫ
    # ──────────────────────────────────────────────────────────────────────────

    {
        "id": "dir_ml_keywords_frameworks",
        "text": "ML/DS ATS-ключевые слова (фреймворки): "
                "Python, PyTorch, TensorFlow, Keras, scikit-learn, XGBoost, LightGBM, CatBoost, "
                "Hugging Face, Transformers, PEFT, LoRA, LangChain, LlamaIndex, "
                "pandas, numpy, scipy, matplotlib, seaborn, plotly.",
        "grade": "any", "direction": "ML", "doc_type": "keywords",
    },
    {
        "id": "dir_ml_keywords_mlops",
        "text": "ML/DS MLOps и деплой ATS-ключевые слова: "
                "MLflow, DVC, Weights & Biases, Airflow, Prefect, FastAPI, Triton, "
                "ONNX, TorchServe, BentoML, Docker, Kubernetes, feature store, "
                "model registry, A/B testing, shadow deployment, data drift.",
        "grade": "any", "direction": "ML", "doc_type": "keywords",
    },
    {
        "id": "dir_ml_achievements",
        "text": "ML достижения-паттерны: "
                "'Обучил модель классификации с accuracy 94.3% (baseline 87%)', "
                "'Разработал pipeline обработки N млн записей в день с помощью Airflow', "
                "'Снизил inference latency модели с 400мс до 45мс через квантизацию и ONNX', "
                "'Занял топ-X% на Kaggle соревновании по [задача]', "
                "'Реализовал RAG-систему поиска по корпусу X документов, MRR@10=0.82'.",
        "grade": "any", "direction": "ML", "doc_type": "achievements",
    },
    {
        "id": "dir_ml_nlp_keywords",
        "text": "ML NLP специализация ключевые слова: "
                "NLP, NER, text classification, sentiment analysis, question answering, "
                "summarization, RAG, embeddings, vector search, FAISS, ChromaDB, "
                "BERT, GPT, LLM, fine-tuning, prompt engineering, tokenization.",
        "grade": "any", "direction": "ML", "doc_type": "keywords",
    },
    {
        "id": "dir_ml_cv_keywords",
        "text": "ML Computer Vision специализация ключевые слова: "
                "Computer Vision, CV, object detection, image segmentation, image classification, "
                "YOLO, ResNet, ViT, OpenCV, albumentations, data augmentation, "
                "mAP, IoU, F1-score, precision, recall, AUC-ROC.",
        "grade": "any", "direction": "ML", "doc_type": "keywords",
    },

    # ──────────────────────────────────────────────────────────────────────────
    # DEVOPS / PLATFORM KEYWORDS И ПАТТЕРНЫ
    # ──────────────────────────────────────────────────────────────────────────

    {
        "id": "dir_devops_keywords_core",
        "text": "DevOps/Platform ATS-ключевые слова (core): "
                "CI/CD, GitLab CI, GitHub Actions, Jenkins, ArgoCD, Flux, "
                "Docker, Kubernetes, Helm, Kustomize, Terraform, Ansible, Pulumi, "
                "AWS, GCP, Azure, Yandex Cloud, EKS, GKE, AKS.",
        "grade": "any", "direction": "DevOps", "doc_type": "keywords",
    },
    {
        "id": "dir_devops_keywords_observability",
        "text": "DevOps наблюдаемость и безопасность ATS-ключевые слова: "
                "Prometheus, Grafana, Loki, Jaeger, OpenTelemetry, ELK Stack, Datadog, "
                "SLO, SLA, SLI, MTTR, MTTD, alerting, on-call, runbooks, "
                "Vault, RBAC, network policies, OPA, Falco.",
        "grade": "any", "direction": "DevOps", "doc_type": "keywords",
    },
    {
        "id": "dir_devops_achievements",
        "text": "DevOps достижения-паттерны: "
                "'Сократил время деплоя с 40 минут до 8 минут через оптимизацию CI-пайплайна', "
                "'Снизил MTTR с 2 часов до 15 минут через алертинг и runbooks', "
                "'Мигрировал N сервисов в Kubernetes, снизив затраты на инфраструктуру на X%', "
                "'Достиг uptime 99.95% за квартал через chaos engineering и улучшение деплой-процесса'.",
        "grade": "any", "direction": "DevOps", "doc_type": "achievements",
    },

    # ──────────────────────────────────────────────────────────────────────────
    # QA KEYWORDS И ПАТТЕРНЫ
    # ──────────────────────────────────────────────────────────────────────────

    {
        "id": "dir_qa_keywords",
        "text": "QA ATS-ключевые слова: "
                "pytest, unittest, Selenium, Playwright, Cypress, Appium, "
                "API testing, Postman, REST Assured, k6, Gatling, JMeter, "
                "BDD, Cucumber, Gherkin, test plan, test cases, regression, smoke, "
                "TDD, code coverage, mutation testing, allure.",
        "grade": "any", "direction": "QA", "doc_type": "keywords",
    },
    {
        "id": "dir_qa_achievements",
        "text": "QA достижения-паттерны: "
                "'Написал N автотестов, покрыв X% критических пользовательских сценариев', "
                "'Настроил запуск автотестов в CI/CD, снизив время регрессии с 4 часов до 30 минут', "
                "'Нашёл и задокументировал N критических багов до релиза', "
                "'Разработал тест-план для нового модуля с нуля, обеспечив 0 P1-багов в продакшене'.",
        "grade": "any", "direction": "QA", "doc_type": "achievements",
    },

    # ──────────────────────────────────────────────────────────────────────────
    # MOBILE KEYWORDS И ПАТТЕРНЫ
    # ──────────────────────────────────────────────────────────────────────────

    {
        "id": "dir_mobile_ios_keywords",
        "text": "iOS разработка ATS-ключевые слова: "
                "Swift, SwiftUI, UIKit, Combine, async/await, XCTest, CocoaPods, SPM, "
                "App Store, TestFlight, CoreData, CoreLocation, Push Notifications, "
                "MVVM, Clean Architecture, Coordinator pattern.",
        "grade": "any", "direction": "Mobile", "doc_type": "keywords",
    },
    {
        "id": "dir_mobile_android_keywords",
        "text": "Android разработка ATS-ключевые слова: "
                "Kotlin, Jetpack Compose, Android SDK, Coroutines, Flow, Room, Retrofit, "
                "Hilt/Dagger, Google Play, Firebase, WorkManager, "
                "MVVM, MVI, Clean Architecture.",
        "grade": "any", "direction": "Mobile", "doc_type": "keywords",
    },
    {
        "id": "dir_mobile_achievements",
        "text": "Mobile достижения-паттерны: "
                "'Опубликовал приложение в App Store / Google Play с N+ скачиваниями', "
                "'Снизил crash rate с X% до Y% за квартал', "
                "'Уменьшил размер приложения на X МБ через оптимизацию ресурсов', "
                "'Реализовал offline-режим приложения, увеличив DAU на X%'.",
        "grade": "any", "direction": "Mobile", "doc_type": "achievements",
    },

    # ──────────────────────────────────────────────────────────────────────────
    # DESIGN KEYWORDS И ПАТТЕРНЫ
    # ──────────────────────────────────────────────────────────────────────────

    {
        "id": "dir_design_keywords",
        "text": "UI/UX Design ATS-ключевые слова: "
                "Figma, Sketch, Adobe XD, Principle, ProtoPie, Zeplin, "
                "дизайн-система, design system, UI-kit, компонентная библиотека, "
                "user research, usability testing, A/B testing, customer journey map, "
                "wireframe, prototype, responsive design, accessibility, WCAG.",
        "grade": "any", "direction": "Design", "doc_type": "keywords",
    },
    {
        "id": "dir_design_achievements",
        "text": "Design достижения-паттерны: "
                "'Разработал дизайн-систему из N компонентов, сократив время дизайна фич на X%', "
                "'Редизайн онбординга увеличил конверсию регистрации с X% до Y%', "
                "'Провёл N пользовательских интервью, выявил X ключевых проблем', "
                "'A/B тест нового дизайна кнопки CTA показал +15% к кликам'.",
        "grade": "any", "direction": "Design", "doc_type": "achievements",
    },

    # ──────────────────────────────────────────────────────────────────────────
    # FULLSTACK KEYWORDS
    # ──────────────────────────────────────────────────────────────────────────

    {
        "id": "dir_fullstack_keywords",
        "text": "Fullstack ATS-ключевые слова: "
                "React, Vue, TypeScript, Node.js, Python, Django, FastAPI, "
                "PostgreSQL, Redis, Docker, REST API, GraphQL, "
                "деплой, DevOps-практики, CI/CD, облачные сервисы.",
        "grade": "any", "direction": "Fullstack", "doc_type": "keywords",
    },
    {
        "id": "dir_fullstack_achievements",
        "text": "Fullstack достижения-паттерны: "
                "'Разработал и запустил продукт в одиночку — от UI до инфраструктуры', "
                "'Реализовал полный цикл фичи: дизайн → фронтенд → бэкенд → деплой за X дней', "
                "'Запустил SaaS-продукт с N активными пользователями'.",
        "grade": "any", "direction": "Fullstack", "doc_type": "achievements",
    },

    # ──────────────────────────────────────────────────────────────────────────
    # GRADE + DIRECTION специфичные советы
    # ──────────────────────────────────────────────────────────────────────────

    {
        "id": "combo_junior_ml",
        "text": "Junior ML специфика: Kaggle-профиль с завершёнными соревнованиями — "
                "сильный сигнал даже без коммерческого опыта. "
                "Указывать метрики моделей: accuracy, F1, AUC. "
                "Pet-проект = реальный датасет + обученная модель + деплой (Streamlit, HuggingFace Spaces). "
                "Курсы: fast.ai, Coursera Andrew Ng, Stepik.",
        "grade": "Junior", "direction": "ML", "doc_type": "advice",
    },
    {
        "id": "combo_senior_ml",
        "text": "Senior ML специфика: обязательны production ML системы. "
                "Описывать: масштаб данных (N млн записей), latency требования, "
                "как решали data drift, как организован переобучение. "
                "Публикации, arxiv, выступления на конференциях — огромный плюс. "
                "MLOps-навыки (мониторинг, feature store, model registry) отличают Senior от Middle.",
        "grade": "Senior", "direction": "ML", "doc_type": "advice",
    },
    {
        "id": "combo_junior_backend",
        "text": "Junior Backend специфика: показывать знание основ HTTP, баз данных и Docker. "
                "Pet-проект обязателен: REST API + БД + докеризация + деплой на VPS/Railway/Render. "
                "Тесты в pet-проекте — огромный плюс и редкость для junior. "
                "Понимание Git, ветвения, PR-процесса — упоминать явно.",
        "grade": "Junior", "direction": "Backend", "doc_type": "advice",
    },
    {
        "id": "combo_lead_backend",
        "text": "Lead Backend специфика: технические решения уровня системы. "
                "Описывать: выбор между технологиями с обоснованием (PostgreSQL vs MongoDB — почему), "
                "управление техдолгом, миграции без даунтайма, "
                "как выстраивал архитектуру под рост нагрузки в X раз. "
                "Найм и техническое собеседование разработчиков.",
        "grade": "Lead", "direction": "Backend", "doc_type": "advice",
    },
    {
        "id": "combo_senior_devops",
        "text": "Senior DevOps специфика: disaster recovery и reliability engineering. "
                "Описывать: как проводил chaos engineering, DR-тесты, "
                "как строил multi-region деплой, как организован on-call. "
                "Platform engineering: внутренние инструменты, developer experience, "
                "self-service инфраструктура для команд разработки.",
        "grade": "Senior", "direction": "DevOps", "doc_type": "advice",
    },

    # ──────────────────────────────────────────────────────────────────────────
    # ОБЩИЕ СОВЕТЫ ПО РЕЗЮМЕ (any grade, any direction)
    # ──────────────────────────────────────────────────────────────────────────

    {
        "id": "general_ats_tips",
        "text": "ATS-оптимизация резюме: использовать те же слова что в вакансии. "
                "Если вакансия говорит 'Python-разработчик' — не писать 'программист на Python'. "
                "Технические аббревиатуры расшифровывать рядом хотя бы раз: CI/CD (Continuous Integration). "
                "Раздел skills должен содержать ключевые слова вакансии — ATS сканирует именно его.",
        "grade": "any", "direction": "any", "doc_type": "advice",
    },
    {
        "id": "general_action_verbs",
        "text": "Сильные глаголы для резюме (начало пунктов): "
                "Разработал, Спроектировал, Реализовал, Оптимизировал, Сократил, Увеличил, "
                "Внедрил, Мигрировал, Автоматизировал, Настроил, Покрыл тестами, "
                "Задеплоил, Запустил, Рефакторил, Устранил, Ускорил, Масштабировал.",
        "grade": "any", "direction": "any", "doc_type": "patterns",
    },
    {
        "id": "general_metrics",
        "text": "Метрики которые HRы ищут в резюме: "
                "Время (сократил с X до Y), Процент (на X%), Масштаб (N пользователей/RPS/записей), "
                "Деньги (сэкономил $X, увеличил revenue на X%), Команда (N разработчиков), "
                "Скорость доставки (time-to-market, deployment frequency). "
                "Если нет точных цифр — примерные лучше чем ничего.",
        "grade": "any", "direction": "any", "doc_type": "advice",
    },
]

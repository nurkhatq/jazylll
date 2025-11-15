"""
Seed data for initial database setup
"""
from sqlalchemy.orm import Session
from app.models.salon import SalonCategory, SubscriptionPlan
import uuid


def seed_categories(db: Session):
    """Seed salon categories"""
    categories = [
        {
            "code": "hair",
            "name_ru": "Парикмахерские услуги",
            "name_kk": "Шаштараз қызметтері",
            "name_en": "Hair Services",
            "description_ru": "Стрижки, укладки, окрашивание волос",
            "description_kk": "Шаш қию, жасау, бояу",
            "description_en": "Haircuts, styling, coloring",
            "sort_order": 1,
        },
        {
            "code": "nails",
            "name_ru": "Ногтевой сервис",
            "name_kk": "Тырнақ қызметі",
            "name_en": "Nail Services",
            "description_ru": "Маникюр, педикюр, наращивание",
            "description_kk": "Маникюр, педикюр, ұзарту",
            "description_en": "Manicure, pedicure, extensions",
            "sort_order": 2,
        },
        {
            "code": "massage",
            "name_ru": "Массаж и СПА",
            "name_kk": "Массаж және СПА",
            "name_en": "Massage & SPA",
            "description_ru": "Массаж, обертывания, релаксация",
            "description_kk": "Массаж, орау, релаксация",
            "description_en": "Massage, wraps, relaxation",
            "sort_order": 3,
        },
        {
            "code": "makeup",
            "name_ru": "Макияж",
            "name_kk": "Макияж",
            "name_en": "Makeup",
            "description_ru": "Повседневный и профессиональный макияж",
            "description_kk": "Күнделікті және кәсіби макияж",
            "description_en": "Everyday and professional makeup",
            "sort_order": 4,
        },
        {
            "code": "epilation",
            "name_ru": "Эпиляция",
            "name_kk": "Эпиляция",
            "name_en": "Hair Removal",
            "description_ru": "Лазерная и восковая эпиляция",
            "description_kk": "Лазерлік және балауыз эпиляция",
            "description_en": "Laser and wax hair removal",
            "sort_order": 5,
        },
        {
            "code": "cosmetology",
            "name_ru": "Косметология",
            "name_kk": "Косметология",
            "name_en": "Cosmetology",
            "description_ru": "Косметологические процедуры",
            "description_kk": "Косметологиялық процедуралар",
            "description_en": "Cosmetology procedures",
            "sort_order": 6,
        },
        {
            "code": "tattoo",
            "name_ru": "Тату и пирсинг",
            "name_kk": "Тату және пирсинг",
            "name_en": "Tattoo & Piercing",
            "description_ru": "Татуировки и пирсинг",
            "description_kk": "Татуировкалар және пирсинг",
            "description_en": "Tattoos and piercing",
            "sort_order": 7,
        },
        {
            "code": "brows_lashes",
            "name_ru": "Брови и ресницы",
            "name_kk": "Қастар және кірпіктер",
            "name_en": "Brows & Lashes",
            "description_ru": "Коррекция бровей, наращивание ресниц",
            "description_kk": "Қас түзету, кірпік ұзарту",
            "description_en": "Brow correction, lash extensions",
            "sort_order": 8,
        },
    ]

    for cat_data in categories:
        existing = db.query(SalonCategory).filter(SalonCategory.code == cat_data["code"]).first()
        if not existing:
            category = SalonCategory(**cat_data)
            db.add(category)

    db.commit()
    print("✓ Salon categories seeded")


def seed_subscription_plans(db: Session):
    """Seed subscription plans"""
    plans = [
        {
            "plan_code": "trial",
            "plan_name_ru": "Пробный период",
            "plan_name_kk": "Сынақ кезеңі",
            "plan_name_en": "Trial",
            "description_ru": "14 дней бесплатно с полным доступом",
            "description_kk": "Толық қол жетімділікпен 14 күн тегін",
            "description_en": "14 days free with full access",
            "monthly_price": 0,
            "features": {
                "max_masters": 999,
                "max_branches": 999,
                "max_monthly_bookings": 999999,
                "has_custom_domain": True,
                "has_advanced_analytics": True,
                "has_api_access": True,
                "priority_support": True,
            },
            "sort_order": 1,
        },
        {
            "plan_code": "basic",
            "plan_name_ru": "Базовый",
            "plan_name_kk": "Негізгі",
            "plan_name_en": "Basic",
            "description_ru": "Для небольших салонов",
            "description_kk": "Шағын салондарға арналған",
            "description_en": "For small salons",
            "monthly_price": 15000,
            "features": {
                "max_masters": 5,
                "max_branches": 3,
                "max_monthly_bookings": 500,
                "has_custom_domain": False,
                "has_advanced_analytics": False,
                "has_api_access": False,
                "priority_support": False,
            },
            "sort_order": 2,
        },
        {
            "plan_code": "professional",
            "plan_name_ru": "Профессиональный",
            "plan_name_kk": "Кәсіби",
            "plan_name_en": "Professional",
            "description_ru": "Для растущего бизнеса",
            "description_kk": "Өсіп келе жатқан бизнеске арналған",
            "description_en": "For growing businesses",
            "monthly_price": 35000,
            "features": {
                "max_masters": 15,
                "max_branches": 10,
                "max_monthly_bookings": 2000,
                "has_custom_domain": True,
                "has_advanced_analytics": True,
                "has_api_access": False,
                "priority_support": True,
            },
            "sort_order": 3,
        },
        {
            "plan_code": "enterprise",
            "plan_name_ru": "Корпоративный",
            "plan_name_kk": "Корпоративтік",
            "plan_name_en": "Enterprise",
            "description_ru": "Для сетей салонов",
            "description_kk": "Салондар желісіне арналған",
            "description_en": "For salon chains",
            "monthly_price": 75000,
            "features": {
                "max_masters": 999,
                "max_branches": 999,
                "max_monthly_bookings": 999999,
                "has_custom_domain": True,
                "has_advanced_analytics": True,
                "has_api_access": True,
                "priority_support": True,
            },
            "sort_order": 4,
        },
    ]

    for plan_data in plans:
        existing = db.query(SubscriptionPlan).filter(SubscriptionPlan.plan_code == plan_data["plan_code"]).first()
        if not existing:
            plan = SubscriptionPlan(**plan_data)
            db.add(plan)

    db.commit()
    print("✓ Subscription plans seeded")


if __name__ == "__main__":
    from app.db.base import SessionLocal

    db = SessionLocal()
    try:
        print("Seeding database...")
        seed_categories(db)
        seed_subscription_plans(db)
        print("Database seeded successfully!")
    finally:
        db.close()

from __future__ import annotations

import json
import os
import random
import sqlite3
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
CORS(app)

DB_NAME = "fitness_coach.db"


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS user_preferences (
            user_id INTEGER PRIMARY KEY,
            primary_goal TEXT,
            experience_level TEXT,
            dietary_preference TEXT,
            allergies TEXT,
            training_frequency INTEGER DEFAULT 3,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS subscriptions (
            user_id INTEGER PRIMARY KEY,
            tier TEXT NOT NULL,
            renewal_date TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS workouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            goal TEXT NOT NULL,
            level TEXT NOT NULL,
            day INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            duration_minutes INTEGER,
            equipment TEXT,
            primary_muscles TEXT,
            instructions TEXT
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS meals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            goal TEXT NOT NULL,
            diet_type TEXT NOT NULL,
            meal_type TEXT NOT NULL,
            title TEXT NOT NULL,
            calories INTEGER,
            protein INTEGER,
            carbs INTEGER,
            fats INTEGER,
            instructions TEXT
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS machine_guides (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            label TEXT UNIQUE NOT NULL,
            machine_name TEXT NOT NULL,
            primary_muscles TEXT,
            cues TEXT,
            instructions TEXT,
            aliases TEXT
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS ads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            image_url TEXT,
            cta_label TEXT,
            cta_url TEXT,
            target_tier TEXT DEFAULT 'ad-supported'
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS user_ad_impressions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            ad_id INTEGER NOT NULL,
            served_on TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (ad_id) REFERENCES ads(id) ON DELETE CASCADE
        )
        """
    )

    conn.commit()
    conn.close()

    seed_initial_content()


def seed_initial_content() -> None:
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM workouts")
    if cursor.fetchone()[0] == 0:
        workouts = [
            (
                "lose_weight",
                "beginner",
                1,
                "Cirkelfys: helkropp",
                "Konditionsfokuserad cirkelträning som kombinerar styrka och puls.",
                30,
                "Kroppsvikt",
                json.dumps(["Ben", "Core", "Axlar"]),
                json.dumps([
                    "Utför jumping jacks i 45 sekunder",
                    "Gå direkt över till knäböj med kroppsvikt",
                    "Avsluta varvet med mountain climbers"
                ]),
            ),
            (
                "lose_weight",
                "beginner",
                2,
                "Intervaller på löpband",
                "Intervallpass som växlar mellan gång och löpning.",
                25,
                "Löpband",
                json.dumps(["Ben", "Hjärta"]),
                json.dumps([
                    "3 minuter uppvärmande gång",
                    "1 minut jogg + 1 minut rask gång, upprepa 8 gånger",
                    "5 minuter nedvarvning"
                ]),
            ),
            (
                "lose_weight",
                "intermediate",
                1,
                "HIIT roddmaskin",
                "Högintensiv intervallträning på roddmaskin.",
                20,
                "Roddmaskin",
                json.dumps(["Rygg", "Ben", "Core"]),
                json.dumps([
                    "90 sekunder rodd på 70 % max",
                    "30 sekunder all-out sprint",
                    "Vila 60 sekunder, upprepa 6 varv"
                ]),
            ),
            (
                "get_fit",
                "beginner",
                1,
                "Helkropp styrka",
                "Stabilitetsinriktad styrketräning med maskiner.",
                40,
                "Maskiner",
                json.dumps(["Bröst", "Rygg", "Ben"]),
                json.dumps([
                    "Benpress 12 reps",
                    "Bröstpress 12 reps",
                    "Latsdrag 12 reps",
                    "Sittande rodd 12 reps"
                ]),
            ),
            (
                "get_fit",
                "beginner",
                2,
                "Rörlighet och core",
                "Lugnare pass med fokus på bål och rörlighet.",
                35,
                "Matta",
                json.dumps(["Core", "Höfter"]),
                json.dumps([
                    "Katt och ko 8 repetitioner",
                    "Planka 3 x 30 sekunder",
                    "Glute bridge 15 repetitioner",
                    "Rotationer i bröstrygg med stretch"
                ]),
            ),
            (
                "build_strength",
                "intermediate",
                1,
                "Överkropp push/pull",
                "Split som fokuserar på press- och dragövningar.",
                50,
                "Fria vikter",
                json.dumps(["Bröst", "Rygg", "Armar"]),
                json.dumps([
                    "Bänkpress 4x8",
                    "Skivstångsrodd 4x8",
                    "Hantelpress lutning 3x10",
                    "Latsdrag smal 3x10"
                ]),
            ),
            (
                "build_strength",
                "intermediate",
                2,
                "Underkropp styrka",
                "Baslyft och unilateral träning för benen.",
                55,
                "Fria vikter",
                json.dumps(["Ben", "Glutes", "Core"]),
                json.dumps([
                    "Knäböj 5x5",
                    "Marklyft 4x5",
                    "Bulgarian split squat 3x8 per ben",
                    "Höftlyft med skivstång 3x10"
                ]),
            ),
        ]
        cursor.executemany(
            """
            INSERT INTO workouts (
                goal, level, day, title, description, duration_minutes,
                equipment, primary_muscles, instructions
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            workouts,
        )

    cursor.execute("SELECT COUNT(*) FROM meals")
    if cursor.fetchone()[0] == 0:
        meals = [
            (
                "lose_weight",
                "standard",
                "breakfast",
                "Proteinrik smoothie",
                320,
                28,
                32,
                8,
                "Mixa grekisk yoghurt, bär, spenat och proteinpulver."
            ),
            (
                "lose_weight",
                "standard",
                "lunch",
                "Kycklingsallad",
                420,
                40,
                30,
                12,
                "Grillad kyckling med quinoa, blandade grönsaker och vinaigrette."
            ),
            (
                "lose_weight",
                "standard",
                "dinner",
                "Ugnsbakad lax",
                480,
                42,
                25,
                18,
                "Servera lax med rostad blomkål och sötpotatis."
            ),
            (
                "lose_weight",
                "vegetarian",
                "lunch",
                "Linsgryta",
                450,
                28,
                60,
                12,
                "Koka röda linser med kokosmjölk, curry och grönsaker."
            ),
            (
                "get_fit",
                "standard",
                "breakfast",
                "Overnight oats",
                380,
                22,
                45,
                12,
                "Havre, mandelmjölk, chiafrön och blåbär i glas över natten."
            ),
            (
                "get_fit",
                "standard",
                "lunch",
                "Fullkornwrap med kalkon",
                520,
                36,
                48,
                16,
                "Fyll en fullkornstortilla med kalkon, hummus och sallad."
            ),
            (
                "build_strength",
                "high_protein",
                "breakfast",
                "Äggröra och havregryn",
                600,
                45,
                55,
                18,
                "Servera äggröra med havregryn och jordnötssmör."
            ),
            (
                "build_strength",
                "high_protein",
                "dinner",
                "Nötfärsbiffar med sötpotatis",
                750,
                55,
                60,
                25,
                "Stek nötfärsbiffar, servera med sötpotatismos och broccoli."
            ),
        ]
        cursor.executemany(
            """
            INSERT INTO meals (
                goal, diet_type, meal_type, title, calories, protein, carbs, fats, instructions
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            meals,
        )

    cursor.execute("SELECT COUNT(*) FROM machine_guides")
    if cursor.fetchone()[0] == 0:
        machine_guides = [
            (
                "leg_press",
                "Benpress",
                json.dumps(["Framsida lår", "Glutes"]),
                json.dumps([
                    "Justera sätet så att knäna är i linje med tårna",
                    "Pressa genom hälarna och håll ryggen mot dynan"
                ]),
                json.dumps([
                    "Placera fötterna höftbrett",
                    "Undvik att låsa knäna i toppläget",
                    "Kontrollera rörelsen på vägen ner"
                ]),
                json.dumps(["leg press", "benpress maskin"])
            ),
            (
                "lat_pulldown",
                "Latsdrag",
                json.dumps(["Lats", "Biceps"]),
                json.dumps([
                    "Greppa stången lite bredare än axelbrett",
                    "Dra ner mot övre bröstet med raka handleder"
                ]),
                json.dumps([
                    "Aktivera skulderbladen innan du drar",
                    "Undvik att dra bakom nacken för att skydda axlarna"
                ]),
                json.dumps(["latsdrag", "lat pulldown"])
            ),
            (
                "rowing_machine",
                "Roddmaskin",
                json.dumps(["Rygg", "Ben", "Core"]),
                json.dumps([
                    "Skjut ifrån med benen först",
                    "Fäll överkroppen lätt bakåt och dra handtaget till nedre bröstet"
                ]),
                json.dumps([
                    "Håll en neutral ryggrad",
                    "Sträck armarna innan du böjer knäna på vägen tillbaka"
                ]),
                json.dumps(["rower", "row machine", "rodd"])
            ),
        ]
        cursor.executemany(
            """
            INSERT INTO machine_guides (label, machine_name, primary_muscles, cues, instructions, aliases)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            machine_guides,
        )

    cursor.execute("SELECT COUNT(*) FROM ads")
    if cursor.fetchone()[0] == 0:
        ads = [
            (
                "Prova premiumprogrammet",
                "Lås upp personliga coachningar och extra recept.",
                "https://example.com/premium.jpg",
                "Uppgradera",
                "https://example.com/premium",
                "ad-supported",
            ),
            (
                "Hälsokosterbjudande",
                "Få 20 % rabatt på proteinpulver och återhämtning.",
                "https://example.com/supplements.jpg",
                "Handla nu",
                "https://example.com/store",
                "ad-supported",
            ),
        ]
        cursor.executemany(
            """
            INSERT INTO ads (title, body, image_url, cta_label, cta_url, target_tier)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ads,
        )

    conn.commit()
    conn.close()


def row_to_dict(row: sqlite3.Row) -> Dict:
    return {key: row[key] for key in row.keys()}


def parse_json_field(field: Optional[str]) -> List[str]:
    if not field:
        return []
    try:
        return json.loads(field)
    except json.JSONDecodeError:
        return []


@app.route("/api/users", methods=["POST"])
def register_user():
    data = request.get_json(force=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password")
    name = (data.get("name") or "").strip()

    if not email or not password:
        return jsonify({"error": "E-post och lösenord krävs."}), 400

    password_hash = generate_password_hash(password)
    now = datetime.utcnow().isoformat()

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (email, password_hash, name, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (email, password_hash, name, now, now),
        )
        user_id = cursor.lastrowid
        cursor.execute(
            "INSERT OR REPLACE INTO subscriptions (user_id, tier, renewal_date) VALUES (?, ?, ?)",
            (user_id, "ad-supported", None),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()
        return jsonify({"error": "E-postadressen används redan."}), 409
    finally:
        conn.close()

    return jsonify({"user_id": user_id, "email": email, "name": name, "subscription": "ad-supported"}), 201


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(force=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()

    if row is None or not password or not check_password_hash(row["password_hash"], password):
        return jsonify({"error": "Ogiltiga inloggningsuppgifter."}), 401

    return jsonify({
        "user_id": row["id"],
        "email": row["email"],
        "name": row["name"],
    })


@app.route("/api/preferences", methods=["POST", "PUT"])
def upsert_preferences():
    data = request.get_json(force=True) or {}
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"error": "user_id krävs."}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO user_preferences (
            user_id, primary_goal, experience_level, dietary_preference, allergies, training_frequency
        ) VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            primary_goal = excluded.primary_goal,
            experience_level = excluded.experience_level,
            dietary_preference = excluded.dietary_preference,
            allergies = excluded.allergies,
            training_frequency = excluded.training_frequency
        """,
        (
            user_id,
            data.get("primary_goal"),
            data.get("experience_level"),
            data.get("dietary_preference"),
            ",".join(data.get("allergies", [])) if isinstance(data.get("allergies"), list) else data.get("allergies"),
            data.get("training_frequency", 3),
        ),
    )
    conn.commit()
    conn.close()

    return jsonify({"message": "Preferenser uppdaterade."})


@app.route("/api/preferences/<int:user_id>", methods=["GET"])
def get_preferences(user_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_preferences WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return jsonify({"error": "Inga preferenser hittades."}), 404

    data = row_to_dict(row)
    allergies = data.get("allergies") or ""
    data["allergies"] = [item for item in allergies.split(",") if item]
    return jsonify(data)


@app.route("/api/plan/workouts", methods=["GET"])
def get_workout_plan():
    user_id = request.args.get("user_id", type=int)
    goal = request.args.get("goal")
    level = request.args.get("level")

    if not goal and user_id:
        pref = _fetch_preferences(user_id)
        goal = pref.get("primary_goal") if pref else None
        level = level or (pref.get("experience_level") if pref else None)

    if not goal:
        return jsonify({"error": "Mål krävs för att skapa träningsplan."}), 400

    if not level:
        level = "beginner"

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM workouts
        WHERE goal = ? AND (level = ? OR level = 'all')
        ORDER BY day ASC
        """,
        (goal, level),
    )
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return jsonify({"error": "Inga pass hittades för det angivna målet."}), 404

    plan: Dict[str, List[Dict]] = {}
    for row in rows:
        day_key = f"dag_{row['day']}"
        plan.setdefault(day_key, []).append(
            {
                "title": row["title"],
                "description": row["description"],
                "duration_minutes": row["duration_minutes"],
                "equipment": row["equipment"],
                "primary_muscles": parse_json_field(row["primary_muscles"]),
                "instructions": parse_json_field(row["instructions"]),
                "level": row["level"],
                "goal": row["goal"],
            }
        )

    return jsonify({
        "goal": goal,
        "level": level,
        "plan": plan,
    })


@app.route("/api/plan/meals", methods=["GET"])
def get_meal_plan():
    user_id = request.args.get("user_id", type=int)
    goal = request.args.get("goal")
    diet_type = request.args.get("diet_type")

    if not goal and user_id:
        pref = _fetch_preferences(user_id)
        goal = pref.get("primary_goal") if pref else None
        diet_type = diet_type or (pref.get("dietary_preference") if pref else None)

    if not goal:
        return jsonify({"error": "Mål krävs för att skapa kostplan."}), 400

    if not diet_type:
        diet_type = "standard"

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM meals
        WHERE goal = ? AND (diet_type = ? OR diet_type = 'standard')
        ORDER BY meal_type
        """,
        (goal, diet_type),
    )
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return jsonify({"error": "Inga måltider hittades för det angivna målet."}), 404

    plan: Dict[str, List[Dict]] = {}
    for row in rows:
        meal_type = row["meal_type"]
        plan.setdefault(meal_type, []).append(
            {
                "title": row["title"],
                "calories": row["calories"],
                "protein": row["protein"],
                "carbs": row["carbs"],
                "fats": row["fats"],
                "instructions": row["instructions"],
                "diet_type": row["diet_type"],
            }
        )

    total_calories = sum(item["calories"] or 0 for meals in plan.values() for item in meals)
    return jsonify({
        "goal": goal,
        "diet_type": diet_type,
        "total_daily_calories": total_calories,
        "plan": plan,
    })


@app.route("/api/machines/identify", methods=["POST"])
def identify_machine():
    data = request.get_json(force=True) or {}
    user_labels = data.get("labels") or []
    manual_hint = data.get("machine_name")

    if not user_labels and not manual_hint:
        return jsonify({"error": "Tillhandahåll minst ett identifierande label eller maskinnamn."}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM machine_guides")
    guides = cursor.fetchall()
    conn.close()

    manual_hint_normalized = manual_hint.lower() if manual_hint else None

    def matches_guide(guide: sqlite3.Row) -> bool:
        labels = parse_json_field(guide["aliases"]) + [guide["label"], guide["machine_name"]]
        labels = [label.lower() for label in labels if label]
        for provided in user_labels:
            if provided.lower() in labels:
                return True
        if manual_hint_normalized and manual_hint_normalized in labels:
            return True
        return False

    matched = next((guide for guide in guides if matches_guide(guide)), None)

    if not matched:
        return jsonify({
            "message": "Ingen exakt träff. Koppla din bildigenkänning till detta endpoint genom att skicka toppetiketter.",
            "labels_tested": user_labels,
        }), 404

    response = {
        "machine_name": matched["machine_name"],
        "primary_muscles": parse_json_field(matched["primary_muscles"]),
        "cues": parse_json_field(matched["cues"]),
        "instructions": parse_json_field(matched["instructions"]),
        "label": matched["label"],
    }

    return jsonify(response)


@app.route("/api/subscription/<int:user_id>", methods=["GET"])
def get_subscription(user_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM subscriptions WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return jsonify({"error": "Ingen prenumeration hittades."}), 404

    return jsonify(row_to_dict(row))


@app.route("/api/subscription", methods=["POST"])
def update_subscription():
    data = request.get_json(force=True) or {}
    user_id = data.get("user_id")
    tier = data.get("tier")

    if not user_id or tier not in {"ad-supported", "premium"}:
        return jsonify({"error": "Ogiltiga prenumerationsuppgifter."}), 400

    renewal_date: Optional[str]
    if tier == "premium":
        renewal_date = (date.today() + timedelta(days=30)).isoformat()
    else:
        renewal_date = None

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO subscriptions (user_id, tier, renewal_date) VALUES (?, ?, ?)",
        (user_id, tier, renewal_date),
    )
    conn.commit()
    conn.close()

    return jsonify({"message": "Prenumerationen uppdaterad.", "tier": tier, "renewal_date": renewal_date})


@app.route("/api/ads/daily", methods=["POST"])
def get_daily_ad():
    data = request.get_json(force=True) or {}
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id krävs."}), 400

    today = date.today().isoformat()

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT tier FROM subscriptions WHERE user_id = ?", (user_id,))
    subscription = cursor.fetchone()

    if subscription is None or subscription["tier"] != "ad-supported":
        conn.close()
        return jsonify({"message": "Ingen reklam behövs för premium."})

    cursor.execute(
        "SELECT * FROM user_ad_impressions WHERE user_id = ? AND served_on = ?",
        (user_id, today),
    )
    if cursor.fetchone():
        conn.close()
        return jsonify({"message": "Dagens reklam har redan visats."})

    cursor.execute(
        "SELECT * FROM ads WHERE target_tier = 'ad-supported' OR target_tier = 'all'"
    )
    ads = cursor.fetchall()

    if not ads:
        conn.close()
        return jsonify({"error": "Inga annonser tillgängliga."}), 404

    ad_row = random.choice(ads)
    cursor.execute(
        "INSERT INTO user_ad_impressions (user_id, ad_id, served_on) VALUES (?, ?, ?)",
        (user_id, ad_row["id"], today),
    )
    conn.commit()
    conn.close()

    ad = row_to_dict(ad_row)
    return jsonify({"ad": ad, "served_on": today})


@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "time": datetime.utcnow().isoformat()}), 200


def _fetch_preferences(user_id: int) -> Optional[Dict]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_preferences WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    data = row_to_dict(row)
    allergies = data.get("allergies") or ""
    data["allergies"] = [item for item in allergies.split(",") if item]
    return data


if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

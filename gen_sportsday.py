#!/usr/bin/env python3
from __future__ import annotations

import random

import pandas as pd
from faker import Faker

FAKER = Faker()
NUM_ENTRIES = 200
FIRST_NAMES = [
    "James", "Robert", "John", "Michael", "William", "David", "Richard", "Joseph", "Thomas", "Charles", "Christopher",
    "Daniel", "Matthew", "Anthony", "Mark", "Donald", "Steven", "Paul", "Andrew", "Joshua", "Kenneth", "Kevin",
    "Brian", "George", "Edward", "Ronald", "Timothy", "Jason", "Jeffrey", "Ryan", "Jacob", "Gary", "Nicholas", "Eric",
    "Jonathan", "Stephen", "Larry", "Justin", "Scott", "Brandon", "Mary", "Patricia", "Jennifer", "Linda", "Elizabeth",
    "Barbara", "Susan", "Jessica", "Sarah", "Karen", "Nancy", "Lisa", "Betty", "Margaret", "Sandra", "Ashley",
    "Kimberly", "Emily", "Donna", "Michelle", "Dorothy", "Carol", "Amanda", "Melissa", "Deborah", "Stephanie",
    "Rebecca", "Sharon", "Laura", "Cynthia", "Kathleen", "Amy", "Shirley", "Angela", "Helen", "Anna", "Brenda",
    "Pamela", "Nicole", "Emma",
]
LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
    "Hernandez", "Lopez", "Gonzales", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee",
    "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker", "Young",
    "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores", "Green", "Adams", "Nelson", "Baker",
    "Hall", "Rivera", "Campbell", "Mitchell", "Carter", "Roberts", "Gomez", "Phillips", "Evans", "Turner", "Diaz",
    "Parker", "Cruz", "Edwards", "Collins", "Reyes",
]
CLASSES = [7, 8, 9, 10, 11, 12]
TEAM_COLORS = ['salmon_red', 'caterpillar_green', 'duckling_yellow', 'whale_blue']

names = set()
while len(names) <= NUM_ENTRIES:
    n = random.choice(FIRST_NAMES), random.choice(LAST_NAMES)
    names.add(n)
names = list(names)

entries = [
    {
        'first_name': names[i][0],
        'last_name': names[i][1],
        'class': random.choice(CLASSES),
        'team_color': random.choice(TEAM_COLORS),
        '100m_running_sec': FAKER.pyfloat(right_digits=2, min_value=11, max_value=20),
        'minigolf_strokes': FAKER.pyint(min_value=18, max_value=72),
        'high_jump_cm': FAKER.pyfloat(right_digits=2, min_value=60, max_value=130),
        'bowling_score': FAKER.pyint(min_value=5, max_value=300),
    }
    for i in range(NUM_ENTRIES)
]

df = pd.DataFrame(entries)
# print(df.drop_duplicates(subset=['first_name', 'last_name']).shape[0])
df.to_csv("sportsday.csv", index=False)

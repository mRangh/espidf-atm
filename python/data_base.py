'''
 * ============================================================================
 * @repo        espidf-atm
 *
 * @author      Marco Antônio Ranghetti
 * @github      github.com/mRangh
 * @email       marcoantonioranghetti@gmail.com
 * @academic    d2026008956@unifei.edu.br
 *
 * @version     1.0.0
 * @date        2026-07-05
 * @license     Apache License 2.0
 * ============================================================================
'''

import sqlite3
from typing import Final
from typing import Tuple

DB_NAME: Final = "atm_db.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bank_accounts (
                u_name TEXT PRIMARY KEY,
                password TEXT,
                money INTEGER
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bank_data (
                bank_hash TEXT PRIMARY KEY,
                total_money INTEGER,
                total_users INTEGER
            )
        ''')

        cursor.execute('''
            INSERT OR REPLACE INTO bank_data (bank_hash, total_money, total_users)
            VALUES ("A1234", 10, 0)
        ''')

        print('[SQLITE]: Database initialized.')

def check_balance(name):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()

        cursor.execute('''
            SELECT money
            FROM bank_accounts
            WHERE u_name = ?
        ''', (name,))
        result_user: Tuple = cursor.fetchone()

        cursor.execute('''
            SELECT total_money
            FROM bank_data
            WHERE bank_hash = "A1234"
        ''')
        result_bank: Tuple = cursor.fetchone()

        result = tuple((result_user[0], result_bank[0]))

        return result

def new_user(u_name, password):
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT u_name
                FROM bank_accounts
                WHERE u_name = ?
            ''', (u_name,))
            result = cursor.fetchone()

            if not result:
                cursor.execute('''
                    INSERT INTO bank_accounts (u_name, password, money)
                    VALUES (?, ?, 3)
                ''', (u_name, password))
                print(f'[SQLITE]: {u_name} registered.')

                cursor.execute('''
                    SELECT total_users
                    FROM bank_data
                    WHERE bank_hash = "A1234"
                ''')
                result_users = cursor.fetchone()[0]

                result_users += 1

                cursor.execute('''
                    UPDATE bank_data
                    SET total_users = ?
                ''', (result_users,))

                return True
            else:
                print(f'[SQLITE_WARN]: {u_name} was alredy registered.')
                return False


    except Exception as e:
        print(f'[SQLITE_ERR]: Could not register {u_name} due to {e}.')
        return False

def atl_balance(u_name, money):
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                SELECT money
                FROM bank_accounts
                WHERE u_name = ?
            ''', (u_name,))

            actual_money = cursor.fetchone()[0]
            atl_money = actual_money + money

            cursor.execute('''
                UPDATE bank_accounts
                SET money = ?
                WHERE u_name = ?
            ''',(atl_money, u_name))

            cursor.execute('''
                SELECT total_money
                FROM bank_data
                WHERE bank_hash = "A1234"
            ''')

            actual_money_bank = cursor.fetchone()[0]
            atl_money_bank = actual_money_bank + money

            cursor.execute('''
                UPDATE bank_data
                SET total_money = ?
                WHERE bank_hash = "A1234"
            ''',(atl_money_bank,))
        print(f'[SQLITE]: Registered {money} in {u_name} account.')
        return True
    except Exception as e:
        print(f'[SQLITE_ERR]: Could not register {money} in {u_name} account due to {e}.')
        return False

def verify_pass(u_name, password):
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                SELECT password
                FROM bank_accounts
                WHERE u_name = ?
            ''',(u_name,))

            return True if cursor.fetchone()[0] == password else False
        print('[SQLITE]: Succesfully verified password.')
    except Exception as e:
        print(f'[SQLITE_ERR]: Could not verify {u_name} password due to {e}')
        return False

def main():
    init_db()
    new_user("abcd1234d5d5d5", "boo590balm612")
    print(f'Is_pass: {verify_pass("abcd1234d5d5d5", "boo590bal612")}')
    print(f'Is_atl: {atl_balance("abcd1234d5d5d5", 5)}')
    print(f'Balance: {check_balance("abcd1234d5d5d5")[0]}')
    return

if __name__ == '__main__':
    main()

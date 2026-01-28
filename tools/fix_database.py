#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'naviport.settings')
django.setup()

from django.db import connection

def fix_database():
    print("=== REPARANDO BASE DE DATOS ===")
    
    with connection.cursor() as cursor:
        try:
            # Verificar si la columna empresa_nombre existe
            cursor.execute("PRAGMA table_info(accounts_user);")
            columns = [row[1] for row in cursor.fetchall()]
            
            print(f"Columnas actuales en accounts_user: {columns}")
            
            if 'empresa_nombre' in columns:
                print("La columna empresa_nombre existe, eliminándola...")
                
                # Crear tabla temporal
                cursor.execute("""
                    CREATE TABLE accounts_user_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        password VARCHAR(128) NOT NULL,
                        last_login DATETIME,
                        is_superuser BOOLEAN NOT NULL,
                        username VARCHAR(150) NOT NULL UNIQUE,
                        first_name VARCHAR(150) NOT NULL,
                        last_name VARCHAR(150) NOT NULL,
                        email VARCHAR(254) NOT NULL,
                        is_staff BOOLEAN NOT NULL,
                        is_active BOOLEAN NOT NULL,
                        date_joined DATETIME NOT NULL,
                        role VARCHAR(20) NOT NULL,
                        cedula_rnc VARCHAR(20) NOT NULL UNIQUE,
                        telefono VARCHAR(15) NOT NULL,
                        empresa_id INTEGER,
                        activo BOOLEAN NOT NULL,
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL,
                        failed_login_attempts INTEGER NOT NULL,
                        is_locked BOOLEAN NOT NULL,
                        locked_until DATETIME,
                        last_login_ip VARCHAR(39),
                        FOREIGN KEY (empresa_id) REFERENCES accounts_empresa (id)
                    );
                """)
                
                # Copiar datos (excluyendo empresa_nombre)
                cursor.execute("""
                    INSERT INTO accounts_user_new (
                        id, password, last_login, is_superuser, username, first_name, last_name,
                        email, is_staff, is_active, date_joined, role, cedula_rnc, telefono,
                        empresa_id, activo, created_at, updated_at, failed_login_attempts,
                        is_locked, locked_until, last_login_ip
                    )
                    SELECT 
                        id, password, last_login, is_superuser, username, first_name, last_name,
                        email, is_staff, is_active, date_joined, role, cedula_rnc, telefono,
                        NULL, activo, created_at, updated_at, failed_login_attempts,
                        is_locked, locked_until, last_login_ip
                    FROM accounts_user;
                """)
                
                # Eliminar tabla vieja y renombrar
                cursor.execute("DROP TABLE accounts_user;")
                cursor.execute("ALTER TABLE accounts_user_new RENAME TO accounts_user;")
                
                print("✅ Columna empresa_nombre eliminada exitosamente")
            else:
                print("✅ La columna empresa_nombre ya no existe")
                
            # Verificar estructura final
            cursor.execute("PRAGMA table_info(accounts_user);")
            columns_after = [row[1] for row in cursor.fetchall()]
            print(f"Columnas después de la reparación: {columns_after}")
            
        except Exception as e:
            print(f"❌ Error reparando base de datos: {e}")
            return False
    
    print("✅ Base de datos reparada exitosamente")
    return True

if __name__ == '__main__':
    fix_database()
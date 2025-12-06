import oracledb
from typing import Dict, List
from datetime import datetime

# --- Configuración de la Conexión ---
# ASEGÚRATE DE QUE ESTOS DATOS SEAN CORRECTOS PARA TU INSTALACIÓN DE ORACLE
DB_USER = "C##CITAS_USER" 
DB_PASS = "CitasPass1" 
DB_HOST = "localhost"
DB_PORT = "1521"
DB_SERVICE = "XEPDB1"
# Cadena de conexión DSN (Data Source Name)
DSN = f"{DB_HOST}:{DB_PORT}/{DB_SERVICE}"

def get_connection():
    """Establece y retorna la conexión a la DB."""
    try:
        # Intento de conexión usando los parámetros definidos
        connection = oracledb.connect(user=DB_USER, password=DB_PASS, dsn=DSN)
        return connection
    except Exception as e:
        # Manejo de errores de conexión críticos
        print(f"Error de conexión con Oracle: {e}") 
        return None

# --- Funciones CRUD ---

def crear_cita(paciente: str, fecha: str, motivo: str) -> int | None:
    """CREATE: Inserta en la tabla CITAS_MEDICAS y retorna el ID generado."""
    
    # Consulta SQL con cláusula RETURNING INTO para obtener el ID de la secuencia
    sql = """
    INSERT INTO CITAS_MEDICAS (PACIENTE_NOMBRE, FECHA_CITA, MOTIVO, ESTADO)
    VALUES (:p_paciente, TO_DATE(:p_fecha, 'YYYY-MM-DD HH24:MI:SS'), :p_motivo, 'Programada')
    RETURNING CITA_ID INTO :new_id
    """
    
    conn = get_connection()
    if not conn:
        print("Fallo al obtener la conexión en crear_cita.")
        return None
        
    new_id = None
    
    try:
        with conn.cursor() as cursor:
            # Creamos una variable de Oracle para recibir el ID de retorno
            new_id_var = cursor.var(oracledb.NUMBER)
            
            # Ejecución de la consulta usando un diccionario de binding
            # El binding previene inyecciones SQL y facilita el paso de variables
            cursor.execute(sql, 
                {
                    'p_paciente': paciente, 
                    'p_fecha': fecha, 
                    'p_motivo': motivo, 
                    'new_id': new_id_var # Variable de retorno
                }
            )
            
            conn.commit()
            # Obtenemos el valor del ID generado y lo convertimos a entero de Python
            new_id = int(new_id_var.getvalue()[0])
            
    except Exception as e:
        print(f"--- ERROR CRÍTICO EN LA INSERCIÓN DE CITA ---")
        print(f"Error de base de datos (Crear): {e}")
        # Deshacemos la transacción en caso de fallo
        conn.rollback() 
        return None
        
    finally:
        if conn:
            # Cerramos la conexión para liberar recursos
            conn.close()
            
    return new_id


def obtener_citas() -> List[Dict]: 
    """READ: Recupera todas las citas y asegura que los nombres de columna sean correctos."""
    sql = "SELECT CITA_ID, PACIENTE_NOMBRE, FECHA_CITA, MOTIVO, ESTADO FROM CITAS_MEDICAS ORDER BY FECHA_CITA"
    conn = get_connection()
    if not conn: return []

    try:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            
            # 1. OBTENER NOMBRES DE COLUMNA EN MAYÚSCULAS
            # Esto es crucial para el mapeo correcto con Pydantic en el API
            column_names = [desc[0].upper() for desc in cursor.description]
            citas_data = cursor.fetchall()
            
            citas = []
            for row in citas_data:
                # 2. CREAR EL DICCIONARIO USANDO LOS NOMBRES EN MAYÚSCULAS
                cita = dict(zip(column_names, row))
                
                # 3. Formateo de fecha/hora
                # Convertimos el objeto datetime de Oracle a string para la API
                if isinstance(cita.get('FECHA_CITA'), datetime):
                    cita['FECHA_CITA'] = cita['FECHA_CITA'].strftime('%Y-%m-%d %H:%M:%S') 
                
                citas.append(cita)
            return citas
    except Exception as e:
        print(f"Error en obtener_citas (mapeo): {e}")
        return []
    finally:
        if conn:
            conn.close()


def actualizar_cita(cita_id: int, estado: str) -> bool:
    sql = "UPDATE CITAS_MEDICAS SET ESTADO = :estado WHERE CITA_ID = :cita_id"
    conn = get_connection()
    if not conn: return False
    try:
        with conn.cursor() as cursor:
            # Ejecución de la operación UPDATE
            cursor.execute(sql, estado=estado, cita_id=cita_id)
            conn.commit()
            # Retornamos True si al menos una fila fue afectada
            return cursor.rowcount > 0 
    except Exception as e:
        print(f"Error en actualizar_cita: {e}")
        conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def eliminar_cita(cita_id: int) -> bool:
    sql = "DELETE FROM CITAS_MEDICAS WHERE CITA_ID = :cita_id"
    conn = get_connection()
    if not conn: return False
    try:
        with conn.cursor() as cursor:
            # Ejecución de la operación DELETE
            cursor.execute(sql, cita_id=cita_id)
            conn.commit()
            # Retornamos True si al menos una fila fue eliminada
            return cursor.rowcount > 0 
    except Exception as e:
        print(f"Error en eliminar_cita: {e}")
        conn.rollback()
        return False
    finally:
        if conn:
            conn.close()
from flask import Blueprint, request, jsonify
from data.database import get_db_connection
import psycopg2
from psycopg2.errors import UniqueViolation

# Cria um Blueprint para a rota de Usuario
usuario_bp = Blueprint('usuario', __name__)

@usuario_bp.route('/add_usuario', methods=['POST'])
def add_usuario():
    conn = None
    cursor = None
    try:
        # Recebe os dados do corpo da requisição
        data = request.json

        # Extrai os campos necessários
        login = data.get('login')
        senha = data.get('senha')

        # Verifica se os dados estão presentes
        if not login or not senha:
            return jsonify({'error': 'Todos os campos são obrigatórios: login e senha'}), 400

        # Conecte ao banco de dados
        conn = get_db_connection()
        cursor = conn.cursor()

        # Insere os dados na tabela Usuario e recupera o ID gerado
        insert_query = """
            INSERT INTO Usuario (login, senha)
            VALUES (%s, %s)
            RETURNING idUsuario; 
        """
        cursor.execute(insert_query, (login, senha))
        usuario_id = cursor.fetchone()[0] 

        conn.commit()

        # Retorna o ID do usuário criado junto com a mensagem de sucesso
        return jsonify({'message': 'Usuário inserido com sucesso!', 'idUsuario': usuario_id}), 201

    except UniqueViolation:
        if conn:
            conn.rollback() 
        return jsonify({'error': 'Login já existe.'}), 409

    except Exception as e:
        if conn:
            conn.rollback() 
        return jsonify({'error': str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Rota para listar todos os usuários
@usuario_bp.route('/get_usuarios', methods=['GET'])
def get_usuarios():
    conn = None
    cursor = None
    try:
        # Conecte ao banco de dados
        conn = get_db_connection()
        cursor = conn.cursor()

        # Executa a consulta SQL para obter todos os usuários
        cursor.execute("SELECT idUsuario, login FROM Usuario")
        usuarios = cursor.fetchall()

        # Formata os dados em uma lista de dicionários
        resultado = []
        for usuario in usuarios:
            resultado.append({
                'idUsuario': usuario[0],
                'login': usuario[1]
            })

        return jsonify({'usuarios': resultado}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@usuario_bp.route('/login', methods=['POST'])
def login():
    conn = None
    cursor = None
    try:
        data = request.json
        login = data.get('login')
        senha = data.get('senha')

        if not login or not senha:
            return jsonify({'error': 'Login e senha são obrigatórios'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. Verificar login e senha na tabela Usuario
        query = "SELECT idUsuario, senha FROM Usuario WHERE login = %s"
        cursor.execute(query, (login,))
        usuario = cursor.fetchone()

        if not usuario or usuario[1] != senha:
            return jsonify({'error': 'Credenciais inválidas'}), 401

        usuario_id = usuario[0]

        # 2. Verificar o tipo de usuário
        tipo_usuario = None
        for tabela in ['Professores', 'Aluno', 'Secretario']:
            query = f"SELECT 1 FROM {tabela} WHERE Usuario_idUsuario = %s"
            cursor.execute(query, (usuario_id,))
            if cursor.fetchone():
                tipo_usuario = tabela.lower() 
                break

        if not tipo_usuario:
            return jsonify({'error': 'Tipo de usuário não encontrado'}), 404

        return jsonify({'message': 'Login bem-sucedido!', 'tipoUsuario': tipo_usuario, 'idUsuario': usuario_id}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
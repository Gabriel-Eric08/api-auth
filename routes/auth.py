import os

from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required
from models import db, Usuario, Sistema, UsuarioSistema
from datetime import datetime

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Rota de login que verifica credenciais, sistema e assinatura do usuário.
    
    Expected JSON body:
    {
        "login": "usuario",
        "senha": "senha123",
        "sistema": "nome_do_sistema"
    }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({"msg": "Nenhum dado fornecido"}), 400
    
    login = data.get('login')
    senha = data.get('senha')
    sistema_nome = data.get('sistema')
    
    # Validação dos campos obrigatórios
    if not login or not senha or not sistema_nome:
        return jsonify({
            "msg": "Campos 'login', 'senha' e 'sistema' são obrigatórios"
        }), 400
    
    # Buscar usuário pelo login
    usuario = Usuario.query.filter_by(login=login).first()
    
    if not usuario or usuario.senha_hash != senha:
        return jsonify({"msg": "Login ou senha inválidos"}), 401
    
    # Buscar sistema pelo nome
    sistema = Sistema.query.filter_by(nome=sistema_nome).first()
    
    if not sistema:
        return jsonify({"msg": "Sistema não encontrado"}), 404
    
    # Verificar se o usuário tem assinatura para este sistema
    assinatura = UsuarioSistema.query.filter_by(
        usuario_id=usuario.id,
        sistema_id=sistema.id
    ).first()
    
    if not assinatura:
        return jsonify({
            "msg": f"Usuário não possui assinatura para o sistema '{sistema_nome}'"
        }), 403
    
    # Verificar se a assinatura está ativa (não expirada)
    if not assinatura.assinatura_ativa():
        return jsonify({
            "msg": f"Assinatura do sistema '{sistema_nome}' expirou em {assinatura.data_exp.strftime('%d/%m/%Y %H:%M')}",
            "data_expiracao": assinatura.data_exp.strftime('%Y-%m-%d %H:%M:%S')
        }), 403
    
    # Criar token JWT com informações do usuário e sistema
    additional_claims = {
        "usuario_id": usuario.id,
        "login": usuario.login,
        "sistema_id": sistema.id,
        "sistema_nome": sistema.nome,
        "db_config": {
            "host": usuario.db_host,
            "port": usuario.db_port,
            "user": usuario.db_user,
            "database": usuario.db_name
        }
    }
    
    access_token = create_access_token(identity=usuario.id, additional_claims=additional_claims)
    
    return jsonify({
        "msg": "Login realizado com sucesso",
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": assinatura.data_exp.strftime('%Y-%m-%d %H:%M:%S'),
        "usuario": {
            "id": usuario.id,
            "login": usuario.login
        },
        "sistema": {
            "id": sistema.id,
            "nome": sistema.nome
        }
    }), 200


@auth_bp.route('/verify', methods=['GET'])
@jwt_required()
def verify_token():
    """
    Rota para verificar se o token JWT é válido.
    """
    return jsonify({
        "msg": "Token válido",
        "status": "authenticated"
    }), 200


@auth_bp.route('/check-signature', methods=['GET'])
@jwt_required()
def check_signature():
    from flask_jwt_extended import get_jwt_identity, get_jwt
    
    claims = get_jwt()
    usuario_id = get_jwt_identity()
    
    usuario = Usuario.query.get(usuario_id)
    if not usuario:
        return jsonify({"msg": "Usuário não encontrado"}), 404
    
    sistema_id = claims.get('sistema_id')
    assinatura = UsuarioSistema.query.filter_by(
        usuario_id=usuario_id,
        sistema_id=sistema_id
    ).first()
    
    if not assinatura:
        return jsonify({"msg": "Assinatura não encontrada"}), 404
    
    return jsonify({
        "assinatura_ativa": assinatura.assinatura_ativa(),
        "data_expiracao": assinatura.data_exp.strftime('%Y-%m-%d %H:%M:%S'),
        "data_criacao": assinatura.data_criacao.strftime('%Y-%m-%d %H:%M:%S'),
        "sistema": assinatura.sistema.nome,
        "dias_restantes": (assinatura.data_exp - datetime.utcnow()).days
    }), 200
@auth_bp.route('/tenant/<restaurante_login>', methods=['GET'])
def get_tenant_config(restaurante_login):

    expected_api_key = os.getenv('JWT_SECRET_KEY')
    client_api_key = request.headers.get('X-System-Api-Key')
    
    if not expected_api_key or client_api_key != expected_api_key:
        return jsonify({"msg": "Acesso não autorizado. Chave de API inválida."}), 401

    usuario = Usuario.query.filter_by(login=restaurante_login).first()
    
    if not usuario:
        return jsonify({"msg": "Restaurante não encontrado"}), 404
    
    sistema = Sistema.query.filter_by(nome="Restaurante").first()
    if sistema:
        assinatura = UsuarioSistema.query.filter_by(
            usuario_id=usuario.id,
            sistema_id=sistema.id
        ).first()
        
        if not assinatura or not assinatura.assinatura_ativa():
            return jsonify({"msg": "Restaurante com assinatura inativa."}), 403

    db_config = {
        "host": usuario.db_host,
        "port": usuario.db_port,
        "user": usuario.db_user,
        "database": usuario.db_name
    }
    
    return jsonify({"db_config": db_config}), 200
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(50), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    
    # Configurações do Banco de Dados do Cliente (Tenant)
    db_host = db.Column(db.String(100), nullable=False)
    db_port = db.Column(db.String(10), default='5432')
    db_user = db.Column(db.String(50), nullable=False)
    db_password = db.Column(db.String(255), nullable=False)
    db_name = db.Column(db.String(50), nullable=False)

    # Relacionamento com os sistemas que ele assina
    assinaturas = db.relationship('UsuarioSistema', backref='usuario', lazy=True)

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def verificar_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)


class Sistema(db.Model):
    __tablename__ = 'sistemas'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), unique=True, nullable=False) # Ex: "Restaurante Pro", "Gestão de Estoque"
    
    # Relacionamento
    usuarios_vinculados = db.relationship('UsuarioSistema', backref='sistema', lazy=True)


class UsuarioSistema(db.Model):
    __tablename__ = 'usuario_sistema'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    sistema_id = db.Column(db.Integer, db.ForeignKey('sistemas.id'), nullable=False)
    
    # Controle de Assinatura
    data_exp = db.Column(db.DateTime, nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)

    def assinatura_ativa(self):
        return self.data_exp > datetime.utcnow()
#!/usr/bin/env python3
"""
Script para inicializar o banco de dados do Šutēru
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.database import create_database, PostgresConnectionFactory

def main():
    """Função principal para inicializar o banco de dados"""
    print("🚀 Inicializando banco de dados do Šutēru...")
    
    try:
        # Testar conexão
        conn = PostgresConnectionFactory.get_connection()
        if conn is None:
            print("❌ Erro: Não foi possível conectar ao banco de dados.")
            print("Verifique se as variáveis de ambiente estão configuradas corretamente.")
            return False
        
        print("✅ Conexão com banco de dados estabelecida.")
        
        # Criar tabelas
        create_database()
        
        print("✅ Banco de dados inicializado com sucesso!")
        print("📝 Tabelas criadas:")
        print("   - users")
        print("   - quizzes") 
        print("   - suggested_questions")
        print("   - user_points")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante a inicialização: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

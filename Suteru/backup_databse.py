import shutil
import datetime
import os

def backup_database():
    # Caminho para o banco de dados original
    source = '/Users/pedroquartiero/Library/Mobile Documents/com~apple~CloudDocs/Coding 2024/Python/Projects/Suteru/sutēru.db'
    
    # Diretório onde os backups serão armazenados
    backup_dir = '/Users/pedroquartiero/Library/Mobile Documents/com~apple~CloudDocs/Coding 2024/Python/Projects/Suteru/backups'
    
    # Certifique-se de que o diretório de backup existe
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    # Nome do arquivo de backup com data e hora
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_filename = f'suteru_backup_{timestamp}.db'
    destination = os.path.join(backup_dir, backup_filename)
    
    # Copia o arquivo de banco de dados para o diretório de backup
    shutil.copy2(source, destination)
    print(f'Backup realizado com sucesso em {destination}')

    # Excluir backups com mais de 7 dias
    for filename in os.listdir(backup_dir):
        filepath = os.path.join(backup_dir, filename)
        if filename.startswith('suteru_backup') and os.path.isfile(filepath):
            file_time = os.path.getmtime(filepath)
            if (datetime.datetime.now() - datetime.datetime.fromtimestamp(file_time)).days > 7:
                os.remove(filepath)
                print(f'Backup antigo excluído: {filepath}')

if __name__ == '__main__':
    backup_database()

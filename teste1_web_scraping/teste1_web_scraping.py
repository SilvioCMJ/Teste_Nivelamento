import os
import requests
from bs4 import BeautifulSoup
import zipfile
from urllib.parse import urljoin

# Configurações
URL = "https://www.gov.br/ans/pt-br/acesso-a-informacao/participacao-da-sociedade/atualizacao-do-rol-de-procedimentos"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_FOLDER = os.path.join(BASE_DIR, "anexos")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "output")
ZIP_NAME = "anexos_ans.zip"

def setup_folders():
    """Cria as pastas necessárias se não existirem"""
    os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def download_file(url, filename):
    """Baixa um arquivo e salva no local especificado"""
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"Erro ao baixar {url}: {str(e)}")
        return False

def find_attachments(soup, base_url):
    """Encontra os links para os anexos I e II com lógica mais precisa"""
    anexos = []
    
    # Mapeamento de identificadores para nomes de arquivo
    anexo_map = {
        'anexo i': 'Anexo_I.pdf',
        'anexo ii': 'Anexo_II.pdf',
        'rol_2021': 'Anexo_I.pdf',  # Identificador específico do Anexo I
        'dut_2021': 'Anexo_II.pdf'  # Identificador específico do Anexo II
    }
    
    # Procurar por todos os links PDF
    for link in soup.find_all('a', href=True):
        href = link['href'].lower()
        
        # Verificar se é um PDF e contém identificadores dos anexos
        if href.endswith('.pdf'):
            for key, filename in anexo_map.items():
                if key in href:
                    full_url = urljoin(base_url, link['href'])
                    anexos.append((filename, full_url))
                    break
    
    # Garantir que encontramos ambos os anexos
    if len(anexos) < 2:
        # Tentar fallback - procurar por texto específico
        for link in soup.find_all('a'):
            text = link.get_text().strip().lower()
            if 'anexo i' in text and link.get('href', '').endswith('.pdf'):
                full_url = urljoin(base_url, link['href'])
                anexos.append(('Anexo_I.pdf', full_url))
            elif 'anexo ii' in text and link.get('href', '').endswith('.pdf'):
                full_url = urljoin(base_url, link['href'])
                anexos.append(('Anexo_II.pdf', full_url))
    
    # Remover duplicatas mantendo a ordem
    seen = set()
    unique_anexos = []
    for item in anexos:
        if item[1] not in seen:
            seen.add(item[1])
            unique_anexos.append(item)
    
    return unique_anexos

def download_attachments(anexos):
    """Baixa todos os anexos encontrados"""
    downloaded_files = []
    for filename, url in anexos:
        filepath = os.path.join(DOWNLOAD_FOLDER, filename)
        print(f"Baixando {filename} de {url}")
        if download_file(url, filepath):
            downloaded_files.append(filepath)
            print(f"Download concluído: {filename}")
        else:
            print(f"Falha ao baixar {filename}")
    return downloaded_files

def create_zip(files):
    """Cria um arquivo ZIP com todos os anexos"""
    zip_path = os.path.join(OUTPUT_FOLDER, ZIP_NAME)
    print(f"Compactando arquivos em {zip_path}")
    
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for file in files:
            if os.path.exists(file):
                zipf.write(file, os.path.basename(file))
            else:
                print(f"Arquivo não encontrado para compactação: {file}")
    
    return zip_path

def main():
    print("Iniciando processo de web scraping...")
    setup_folders()
    
    try:
        # Acessar o site
        print(f"Acessando {URL}...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(URL, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Encontrar anexos
        anexos = find_attachments(soup, URL)
        if len(anexos) < 2:
            print("Não foi possível encontrar ambos os anexos!")
            print("Links encontrados:")
            for name, url in anexos:
                print(f"- {name}: {url}")
            return
        
        print(f"Encontrados {len(anexos)} anexos:")
        for name, url in anexos:
            print(f"- {name}: {url}")
        
        # Baixar anexos
        downloaded_files = download_attachments(anexos)
        if len(downloaded_files) < 2:
            print("Não foi possível baixar todos os anexos!")
            return
        
        # Compactar
        zip_path = create_zip(downloaded_files)
        
        print("\nProcesso concluído com sucesso!")
        print(f"Arquivos baixados em: {DOWNLOAD_FOLDER}")
        print(f"Arquivo ZIP criado em: {zip_path}")
    
    except Exception as e:
        print(f"Erro durante o processo: {str(e)}")

if __name__ == "__main__":
    main()
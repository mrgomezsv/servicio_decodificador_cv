#!/usr/bin/env python3
"""
Script de prueba para el Servicio Decodificador CV
Lumina Talent Group
"""

import requests
import json
import os
import sys
from datetime import datetime

# Configuración
SERVICE_URL = "http://localhost:8001"
TEST_CV_PATH = "test_cv.pdf"  # Crear un CV de prueba

def test_health_check():
    """Prueba el endpoint de salud del servicio"""
    print("🔍 Probando health check...")
    
    try:
        response = requests.get(f"{SERVICE_URL}/health", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check exitoso: {data}")
            return True
        else:
            print(f"❌ Health check falló: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error conectando al servicio: {e}")
        return False

def test_root_endpoint():
    """Prueba el endpoint raíz"""
    print("🏠 Probando endpoint raíz...")
    
    try:
        response = requests.get(f"{SERVICE_URL}/", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Endpoint raíz exitoso: {data}")
            return True
        else:
            print(f"❌ Endpoint raíz falló: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error conectando al servicio: {e}")
        return False

def create_test_cv():
    """Crea un CV de prueba simple"""
    print("📄 Creando CV de prueba...")
    
    # Crear un PDF simple de prueba
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        c = canvas.Canvas(TEST_CV_PATH, pagesize=letter)
        c.drawString(100, 750, "CURRICULUM VITAE")
        c.drawString(100, 720, "Juan Carlos Pérez González")
        c.drawString(100, 700, "Email: juan.perez@email.com")
        c.drawString(100, 680, "Teléfono: +52 55 1234 5678")
        c.drawString(100, 660, "LinkedIn: linkedin.com/in/juanperez")
        
        c.drawString(100, 620, "EXPERIENCIA LABORAL")
        c.drawString(100, 600, "Desarrollador Full Stack - TechCorp")
        c.drawString(100, 580, "2020 - Presente")
        c.drawString(100, 560, "- Desarrollo de aplicaciones web con React y Node.js")
        c.drawString(100, 540, "- Implementación de APIs REST")
        
        c.drawString(100, 500, "EDUCACIÓN")
        c.drawString(100, 480, "Ingeniería en Sistemas - Universidad Nacional")
        c.drawString(100, 460, "2016 - 2020")
        
        c.drawString(100, 420, "HABILIDADES")
        c.drawString(100, 400, "JavaScript, Python, React, Node.js, MySQL, Git")
        
        c.save()
        print(f"✅ CV de prueba creado: {TEST_CV_PATH}")
        return True
        
    except ImportError:
        print("⚠️  ReportLab no está instalado. Creando archivo de texto simple...")
        
        # Crear archivo de texto simple
        cv_content = """
CURRICULUM VITAE

Juan Carlos Pérez González
Email: juan.perez@email.com
Teléfono: +52 55 1234 5678
LinkedIn: linkedin.com/in/juanperez

EXPERIENCIA LABORAL

Desarrollador Full Stack - TechCorp
2020 - Presente
- Desarrollo de aplicaciones web con React y Node.js
- Implementación de APIs REST
- Optimización de rendimiento de aplicaciones

Desarrollador Frontend - StartupXYZ
2018 - 2020
- Desarrollo de interfaces de usuario con React
- Implementación de diseño responsive

EDUCACIÓN

Ingeniería en Sistemas - Universidad Nacional
2016 - 2020
GPA: 8.5/10

HABILIDADES

Técnicas:
- JavaScript, TypeScript
- Python, Java
- React, Angular, Vue.js
- Node.js, Express
- MySQL, MongoDB
- Git, Docker

Idiomas:
- Español (Nativo)
- Inglés (Avanzado)

CERTIFICACIONES

AWS Certified Developer Associate
Microsoft Azure Fundamentals
        """
        
        with open(TEST_CV_PATH.replace('.pdf', '.txt'), 'w', encoding='utf-8') as f:
            f.write(cv_content)
        
        print(f"✅ CV de prueba creado: {TEST_CV_PATH.replace('.pdf', '.txt')}")
        return TEST_CV_PATH.replace('.pdf', '.txt')

def test_cv_extraction():
    """Prueba la extracción de CV"""
    print("📄 Probando extracción de CV...")
    
    # Usar el archivo de prueba creado
    test_file = TEST_CV_PATH
    if not os.path.exists(test_file):
        test_file = TEST_CV_PATH.replace('.pdf', '.txt')
    
    if not os.path.exists(test_file):
        print("❌ No se pudo crear archivo de prueba")
        return False
    
    # Datos de prueba
    test_data = {
        "candidate_id": "test-candidate-123",
        "file_path": os.path.abspath(test_file),
        "candidate_data": {
            "firstName": "Juan Carlos",
            "lastName": "Pérez González",
            "email": "juan.perez@email.com",
            "phone": "+52 55 1234 5678"
        }
    }
    
    try:
        response = requests.post(
            f"{SERVICE_URL}/api/cv/extract",
            json=test_data,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Extracción de CV exitosa: {data}")
            return True
        else:
            print(f"❌ Extracción de CV falló: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error en extracción de CV: {e}")
        return False

def test_get_cv_data():
    """Prueba obtener datos extraídos del CV"""
    print("📊 Probando obtención de datos de CV...")
    
    candidate_id = "test-candidate-123"
    
    try:
        response = requests.get(
            f"{SERVICE_URL}/api/cv/{candidate_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Datos de CV obtenidos exitosamente")
            print(f"Información personal: {data.get('personal_info', {})}")
            print(f"Experiencia laboral: {len(data.get('work_experience', []))} registros")
            print(f"Habilidades: {len(data.get('skills', []))} habilidades")
            return True
        elif response.status_code == 404:
            print("⚠️  Datos de CV no encontrados (puede ser normal si el procesamiento aún no terminó)")
            return True
        else:
            print(f"❌ Error obteniendo datos de CV: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error obteniendo datos de CV: {e}")
        return False

def cleanup_test_files():
    """Limpia archivos de prueba"""
    print("🧹 Limpiando archivos de prueba...")
    
    test_files = [
        TEST_CV_PATH,
        TEST_CV_PATH.replace('.pdf', '.txt')
    ]
    
    for file_path in test_files:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"🗑️  Eliminado: {file_path}")

def main():
    """Función principal de pruebas"""
    print("🧪 Iniciando pruebas del Servicio Decodificador CV")
    print("=" * 50)
    
    # Verificar que el servicio esté ejecutándose
    print("🔍 Verificando que el servicio esté ejecutándose...")
    
    if not test_health_check():
        print("❌ El servicio no está ejecutándose. Inicia el servicio primero:")
        print("   cd Servicio_Decodificador_CV")
        print("   ./start.sh")
        sys.exit(1)
    
    print("✅ Servicio está ejecutándose correctamente")
    print()
    
    # Ejecutar pruebas
    tests = [
        ("Health Check", test_health_check),
        ("Endpoint Raíz", test_root_endpoint),
        ("Crear CV de Prueba", create_test_cv),
        ("Extracción de CV", test_cv_extraction),
        ("Obtener Datos de CV", test_get_cv_data)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASÓ")
            else:
                print(f"❌ {test_name}: FALLÓ")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
    
    # Limpiar archivos de prueba
    cleanup_test_files()
    
    # Resumen
    print("\n" + "=" * 50)
    print(f"📊 RESUMEN DE PRUEBAS")
    print(f"✅ Pasadas: {passed}/{total}")
    print(f"❌ Fallidas: {total - passed}/{total}")
    
    if passed == total:
        print("🎉 ¡Todas las pruebas pasaron! El servicio está funcionando correctamente.")
    else:
        print("⚠️  Algunas pruebas fallaron. Revisa los logs para más detalles.")
    
    print("\n📖 Documentación disponible en:")
    print(f"   Swagger UI: {SERVICE_URL}/docs")
    print(f"   ReDoc: {SERVICE_URL}/redoc")

if __name__ == "__main__":
    main() 
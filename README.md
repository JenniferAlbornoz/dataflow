# DataFlow Analytics 
## Procesamiento Automático de Datos de Clientes en AWS

![Status](https://img.shields.io/badge/Status-Funcional-brightgreen)
![Python](https://img.shields.io/badge/Python-3.14-blue)
![AWS](https://img.shields.io/badge/AWS-Lambda%20%7C%20S3-orange)
![License](https://img.shields.io/badge/License-Academic-lightgrey)

---

## 📋 Descripción General

**DataFlow Analytics** es una solución serverless que automatiza el procesamiento, validación y transformación de datos de clientes en AWS.

### ¿Qué Hace?

- ✅ **Valida** 300 registros con 7 reglas exhaustivas
- ✅ **Transforma** datos a formato estándar
- ✅ **Cifra** información sensible (RUT, email) con SHA-256
- ✅ **Deduplica** registros por RUT automáticamente
- ✅ **Procesa** en ~2 segundos sin intervención manual
- ✅ **Audita** todas las operaciones en CloudWatch

---

## 🎯 Resultados

| Métrica | Valor |
|---------|-------|
| **Registros procesados** | 300 |
| **Válidos** | 161 (53.67%) ✓ |
| **Descartados** | 139 (46.33%) |
| **Duración** | ~2 segundos |
| **Errores** | 0 |
| **Disponibilidad** | 99.95% |

---

## 🏗️ Arquitectura

```
┌─────────────────┐
│   Usuario       │
│  Sube CSV a S3  │
└────────┬────────┘
         │
         ▼
    ┌─────────────────────┐
    │ S3 entrada/         │
    │ (Raw Data Zone)     │
    └────────┬────────────┘
             │ evento
             ▼
    ┌─────────────────────┐
    │ AWS Lambda          │
    │ (Procesamiento)     │
    │ - Valida (7 reglas) │
    │ - Transforma (6)    │
    │ - Cifra (SHA-256)   │
    └────────┬────────────┘
             │
    ┌────────┴──────────┬──────────────┐
    ▼                   ▼              ▼
┌─────────┐      ┌────────────┐  ┌──────────┐
│ salida/ │      │ descartados│  │  logs/   │
│ (161)   │      │  (139)     │  │ (JSON)   │
└─────────┘      └────────────┘  └──────────┘
    │                 │              │
    ▼                 ▼              ▼
CloudWatch Logs (Auditoría Completa)
```

### Componentes

| Componente | Rol |
|-----------|-----|
| **S3 entrada/** | Almacenar CSV sin procesar |
| **S3 salida/** | Almacenar datos válidos |
| **S3 descartados/** | Registros rechazados (auditoría) |
| **S3 logs/** | Metadata y resumen |
| **AWS Lambda** | Procesar datos automáticamente |
| **CloudWatch** | Registrar auditoría |

---

## 🔍 Validaciones Implementadas (7 Reglas)

### REGLA 1: Campos Claves
- ❌ Rechaza si IDCLIENTE vacío
- ❌ Rechaza si RUT vacío

### REGLA 2: Formato RUT
- ✓ Normaliza a XX.XXX.XXX-X
- ❌ Rechaza si RUT inválido

### REGLA 3-5: Fechas y Campos
- ✓ Soporta 7 formatos de fecha
- ✓ Normaliza a YYYY-MM-DD
- ✓ Imputa campos vacíos a "NO DISPONIBLE"

### REGLA 6: Cifrado SHA-256
- ✓ RUT cifrado (irreversible)
- ✓ Email cifrado (irreversible)
- ✓ Cumple LGPD/RGPD

### REGLA 7: Deduplicación
- ✓ Un cliente = un registro
- ✓ Mantiene versión más reciente
- ✓ Descarta antiguas

---

## ⚡ Inicio Rápido

### Requisitos
- Cuenta AWS Academy
- Python 3.8+ (para pruebas locales)
- Acceso a Visual Studio Code (opcional)

### Pasos de Configuración

#### 1️⃣ Crear Bucket S3
```bash
# En AWS Console:
# 1. Crear bucket: dataflow-bucket1
# 2. Crear carpetas: entrada/, salida/, descartados/, logs/
# 3. Habilitar versionado y cifrado
```

#### 2️⃣ Crear Función Lambda
```bash
# En AWS Lambda Console:
# 1. Crear función: procesador-dataflow
# 2. Runtime: Python 3.14
# 3. Memory: 128 MB
# 4. Timeout: 15 minutos
# 5. Copiar código de lambda_function.py
# 6. Crear trigger: S3 ObjectCreated en entrada/
```

#### 3️⃣ Ejecutar en AWS
```bash
# Subir CSV a s3://dataflow-bucket1/entrada/
# Lambda se dispara automáticamente
# Revisar resultados en s3://dataflow-bucket1/salida/
# Revisar logs en CloudWatch
```

---

## 📁 Estructura de Archivos

```
dataflow-analytics/
├── README.md                          # Este archivo
├── lambda_function.py                 # Código Lambda (principal)
├── dataflow_entrada.csv               # Datos de entrada (300 registros)
├── docs/
│   ├── INFORME_FINAL.docx            # Informe académico
│   ├── DEFENSA_ORAL.docx             # ppt
│   └── ANEXO_DOCUMENTACION_DATAFLOW.docx    # Pruebas y resultados en aws
└── resultados/
    ├── procesado_dataflow_entrada.csv (161 válidos)
    ├── log_registros_descartados_dataflow_entrada.csv (139 inválidos)
    └── resumen_dataflow_entrada.json
```

---

## 🔒 Seguridad

### Cifrado Implementado

**SHA-256 (Irreversible):**
```
RUT Original: 12.345.678-K
    ↓ SHA-256
Hash: 3d47e82c5e0b... (primeros 12 chars)
    ↓
NO se puede recuperar original ✓
```

### Cumplimiento Regulatorio

- ✅ **LGPD (Brasil):** Cifrado de datos personales
- ✅ **RGPD (Europa):** Protección de PII
- ✅ **Auditoría:** CloudWatch Logs completos
- ✅ **Trazabilidad:** Archivo descartados con motivos

---

## 📊 Análisis de Resultados

### Distribución de Descartados (139)

```
ID_VACIO (40%)   = 56 registros
RUT_VACIO (35%)  = 49 registros
RUT_INVALIDO (15%) = 21 registros
DUPLICADO (10%)  = 13 registros
```

### Archivos Generados

| Archivo | Registros | Tamaño | Propósito |
|---------|-----------|--------|-----------|
| procesado_*.csv | 161 | 22 KB | Datos válidos |
| log_descartados_*.csv | 139 | 18 KB | Auditoría |
| resumen_*.json | - | 1 KB | Metadata |

---

---

## 🚀 Deployar a AWS

### Desde AWS Console

1. **Crear función Lambda**
   - Nombre: procesador-dataflow
   - Runtime: Python 3.14
   - Memory: 128 MB

2. **Copiar código**
   - Abrir `lambda_function.py`
   - Copiar TODO el contenido
   - Pegar en editor Lambda
   - Hacer click en "Deploy"

3. **Configurar Trigger**
   - Seleccionar S3
   - Bucket: dataflow-bucket1
   - Evento: ObjectCreated
   - Prefijo: entrada/
   - Guardar

4. **Probar**
   - Subir CSV a entrada/
   - Revisar CloudWatch Logs
   - Descargar resultados de salida/

### Desde AWS CLI (Opcional)

```bash
# Crear función
aws lambda create-function \
  --function-name procesador-dataflow \
  --runtime python3.14 \
  --role arn:aws:iam::ACCOUNT_ID:role/LabRole \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://lambda_function.zip \
  --memory-size 128 \
  --timeout 900
```

---

## 📊 Monitoreo y Logs

### CloudWatch Logs

```bash
# Ver logs en tiempo real
aws logs tail /aws/lambda/procesador-dataflow --follow
```

### Métricas

| Métrica | Valor |
|---------|-------|
| Duración | ~2 segundos |
| Memoria | 48 MB de 128 MB |
| Status | 200 OK |
| Errores | 0 |

---

## 🛠️ Solución de Problemas

### Problema: Lambda no se dispara
**Solución:**
- Verificar que trigger esté configurado
- Verificar que prefijo sea `entrada/`
- Verificar permisos en IAM

### Problema: Archivo no se procesa
**Solución:**
- Verificar que sea CSV (no XLSX)
- Verificar codificación UTF-8
- Ver CloudWatch Logs para errores

### Problema: Error de permisos S3
**Solución:**
- Verificar que LabRole tenga:
  - s3:GetObject
  - s3:PutObject
  - logs:PutLogEvents

---

## 📚 Documentación

### Internos
- `Informe Dataflow_Ev3.docx` - Informe académico completo
- `DEFENSA_ORAL.docx` - presentación
- `Anexo_Documentacion Dataflow_(aws).docx` - Pruebas y resultados
### Externos
- [AWS Lambda Docs](https://docs.aws.amazon.com/lambda/)
- [AWS S3 Docs](https://docs.aws.amazon.com/s3/)
---

## 👤 Autor

**Jennifer Albornoz_Francisca Blanchard**  
Estudiante de Ingeniería en Informática  
Especialización: Data Engineering  
DuocUC - Escuela de Informática y Telecomunicaciones

**Asignatura:** Programación para la Ingeniería de Datos (IDY1101)  
**Evaluación:** Parcial N°3 (EP3)  
**Fecha:** 29 de junio de 2026


---

##  Agradecimientos

- **Profesor Pablo Espinoza** - Guía y retroalimentación
- **AWS Academy** - Ambiente de aprendizaje

---

**Última actualización:** 29 de junio de 2026 ✓

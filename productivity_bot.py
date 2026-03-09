# -*- coding: utf-8 -*-

“””
Bot de Productividad para Telegram
Funcionalidades: Tareas, Habitos, Pomodoro Timer, Estadisticas
Compatible con iOS (Carnets) y hosting gratuito
“””

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import sqlite3
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import io
import os

# Configuracion de logging

logging.basicConfig(
format=’%(asctime)s - %(name)s - %(levelname)s - %(message)s’,
level=logging.INFO
)
logger = logging.getLogger(**name**)

# ============================================

# BASE DE DATOS

# ============================================

def init_db():
“”“Inicializar base de datos SQLite”””
conn = sqlite3.connect(‘productivity.db’)
c = conn.cursor()

```
# Tabla de tareas
c.execute('''CREATE TABLE IF NOT EXISTS tasks
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              user_id INTEGER,
              task TEXT,
              completed INTEGER DEFAULT 0,
              created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
              completed_at TIMESTAMP)''')

# Tabla de habitos
c.execute('''CREATE TABLE IF NOT EXISTS habits
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              user_id INTEGER,
              habit_name TEXT,
              created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

# Tabla de registro de habitos
c.execute('''CREATE TABLE IF NOT EXISTS habit_logs
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              habit_id INTEGER,
              user_id INTEGER,
              logged_at DATE DEFAULT CURRENT_TIMESTAMP)''')

# Tabla de sesiones Pomodoro
c.execute('''CREATE TABLE IF NOT EXISTS pomodoro
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              user_id INTEGER,
              duration INTEGER,
              task_name TEXT,
              completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

conn.commit()
conn.close()
```

# ============================================

# COMANDOS PRINCIPALES

# ============================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
“”“Comando /start - Menu principal”””
keyboard = [
[InlineKeyboardButton(“📝 Tareas”, callback_data=‘menu_tasks’),
InlineKeyboardButton(“🎯 Habitos”, callback_data=‘menu_habits’)],
[InlineKeyboardButton(“🍅 Pomodoro”, callback_data=‘menu_pomodoro’),
InlineKeyboardButton(“📊 Estadisticas”, callback_data=‘menu_stats’)],
[InlineKeyboardButton(“❓ Ayuda”, callback_data=‘help’)]
]
reply_markup = InlineKeyboardMarkup(keyboard)

```
welcome_text = """
```

🤖 *Bot de Productividad*

¡Bienvenido! Aqui puedes:

📝 *Tareas*: Gestiona tu lista de pendientes
🎯 *Habitos*: Crea y rastrea habitos diarios
🍅 *Pomodoro*: Temporizador de productividad
📊 *Estadisticas*: Visualiza tu progreso

Selecciona una opcion para comenzar:
“””

```
if update.message:
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
else:
    await update.callback_query.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
```

# ============================================

# TAREAS

# ============================================

async def menu_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
“”“Menu de tareas”””
query = update.callback_query
await query.answer()

```
keyboard = [
    [InlineKeyboardButton("➕ Nueva Tarea", callback_data='task_new')],
    [InlineKeyboardButton("📋 Ver Tareas", callback_data='task_list')],
    [InlineKeyboardButton("✅ Completar Tarea", callback_data='task_complete')],
    [InlineKeyboardButton("🗑 Eliminar Tarea", callback_data='task_delete')],
    [InlineKeyboardButton("« Volver", callback_data='back_main')]
]
reply_markup = InlineKeyboardMarkup(keyboard)

await query.edit_message_text(
    "📝 *Gestion de Tareas*\n\n¿Que deseas hacer?",
    reply_markup=reply_markup,
    parse_mode='Markdown'
)
```

async def task_new(update: Update, context: ContextTypes.DEFAULT_TYPE):
“”“Solicitar nueva tarea”””
query = update.callback_query
await query.answer()

```
context.user_data['waiting_for'] = 'new_task'
await query.edit_message_text(
    "✍️ Escribe tu nueva tarea:\n\n(Escribe /cancelar para cancelar)"
)
```

async def task_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
“”“Listar todas las tareas”””
query = update.callback_query
await query.answer()

```
user_id = query.from_user.id
conn = sqlite3.connect('productivity.db')
c = conn.cursor()

c.execute('''SELECT id, task, completed FROM tasks 
             WHERE user_id = ? ORDER BY completed, created_at DESC''', (user_id,))
tasks = c.fetchall()
conn.close()

if not tasks:
    text = "📭 No tienes tareas registradas.\n\nUsa *Nueva Tarea* para agregar una."
else:
    text = "📋 *Tus Tareas:*\n\n"
    pending = [t for t in tasks if t[2] == 0]
    completed = [t for t in tasks if t[2] == 1]
    
    if pending:
        text += "*Pendientes:*\n"
        for task in pending:
            text += f"▫️ {task[0]}. {task[1]}\n"
    
    if completed:
        text += f"\n*Completadas:* ({len(completed)})\n"
        for task in completed[:5]:  # Mostrar solo las ultimas 5
            text += f"✅ ~~{task[1]}~~\n"

keyboard = [[InlineKeyboardButton("« Volver", callback_data='menu_tasks')]]
reply_markup = InlineKeyboardMarkup(keyboard)

await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
```

async def task_complete(update: Update, context: ContextTypes.DEFAULT_TYPE):
“”“Completar tarea”””
query = update.callback_query
await query.answer()

```
user_id = query.from_user.id
conn = sqlite3.connect('productivity.db')
c = conn.cursor()

c.execute('''SELECT id, task FROM tasks 
             WHERE user_id = ? AND completed = 0 
             ORDER BY created_at''', (user_id,))
tasks = c.fetchall()
conn.close()

if not tasks:
    keyboard = [[InlineKeyboardButton("« Volver", callback_data='menu_tasks')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        "✅ ¡No tienes tareas pendientes!",
        reply_markup=reply_markup
    )
    return

keyboard = []
for task in tasks:
    keyboard.append([InlineKeyboardButton(
        f"✓ {task[1][:30]}...", 
        callback_data=f'complete_{task[0]}'
    )])
keyboard.append([InlineKeyboardButton("« Volver", callback_data='menu_tasks')])
reply_markup = InlineKeyboardMarkup(keyboard)

await query.edit_message_text(
    "Selecciona la tarea a completar:",
    reply_markup=reply_markup
)
```

async def task_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
“”“Eliminar tarea”””
query = update.callback_query
await query.answer()

```
user_id = query.from_user.id
conn = sqlite3.connect('productivity.db')
c = conn.cursor()

c.execute('''SELECT id, task, completed FROM tasks 
             WHERE user_id = ? 
             ORDER BY completed, created_at DESC''', (user_id,))
tasks = c.fetchall()
conn.close()

if not tasks:
    keyboard = [[InlineKeyboardButton("« Volver", callback_data='menu_tasks')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        "📭 No tienes tareas para eliminar.",
        reply_markup=reply_markup
    )
    return

keyboard = []
for task in tasks:
    status = "✅" if task[2] else "▫️"
    keyboard.append([InlineKeyboardButton(
        f"🗑 {status} {task[1][:25]}...", 
        callback_data=f'delete_{task[0]}'
    )])
keyboard.append([InlineKeyboardButton("« Volver", callback_data='menu_tasks')])
reply_markup = InlineKeyboardMarkup(keyboard)

await query.edit_message_text(
    "Selecciona la tarea a eliminar:",
    reply_markup=reply_markup
)
```

# ============================================

# HABITOS

# ============================================

async def menu_habits(update: Update, context: ContextTypes.DEFAULT_TYPE):
“”“Menu de habitos”””
query = update.callback_query
await query.answer()

```
keyboard = [
    [InlineKeyboardButton("➕ Nuevo Habito", callback_data='habit_new')],
    [InlineKeyboardButton("📋 Mis Habitos", callback_data='habit_list')],
    [InlineKeyboardButton("✅ Registrar Hoy", callback_data='habit_log')],
    [InlineKeyboardButton("🔥 Rachas", callback_data='habit_streaks')],
    [InlineKeyboardButton("« Volver", callback_data='back_main')]
]
reply_markup = InlineKeyboardMarkup(keyboard)

await query.edit_message_text(
    "🎯 *Seguimiento de Habitos*\n\n¿Que deseas hacer?",
    reply_markup=reply_markup,
    parse_mode='Markdown'
)
```

async def habit_new(update: Update, context: ContextTypes.DEFAULT_TYPE):
“”“Solicitar nuevo habito”””
query = update.callback_query
await query.answer()

```
context.user_data['waiting_for'] = 'new_habit'
await query.edit_message_text(
    "✍️ Escribe el nombre de tu nuevo habito:\n\n(Escribe /cancelar para cancelar)"
)
```

async def habit_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
“”“Listar habitos”””
query = update.callback_query
await query.answer()

```
user_id = query.from_user.id
conn = sqlite3.connect('productivity.db')
c = conn.cursor()

c.execute('SELECT id, habit_name FROM habits WHERE user_id = ?', (user_id,))
habits = c.fetchall()
conn.close()

if not habits:
    text = "📭 No tienes habitos registrados.\n\nUsa *Nuevo Habito* para agregar uno."
else:
    text = "🎯 *Tus Habitos:*\n\n"
    for habit in habits:
        text += f"▫️ {habit[1]}\n"

keyboard = [[InlineKeyboardButton("« Volver", callback_data='menu_habits')]]
reply_markup = InlineKeyboardMarkup(keyboard)

await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
```

async def habit_log(update: Update, context: ContextTypes.DEFAULT_TYPE):
“”“Registrar habito de hoy”””
query = update.callback_query
await query.answer()

```
user_id = query.from_user.id
conn = sqlite3.connect('productivity.db')
c = conn.cursor()

c.execute('SELECT id, habit_name FROM habits WHERE user_id = ?', (user_id,))
habits = c.fetchall()
conn.close()

if not habits:
    keyboard = [[InlineKeyboardButton("« Volver", callback_data='menu_habits')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        "📭 No tienes habitos para registrar.",
        reply_markup=reply_markup
    )
    return

keyboard = []
for habit in habits:
    keyboard.append([InlineKeyboardButton(
        f"✓ {habit[1]}", 
        callback_data=f'log_{habit[0]}'
    )])
keyboard.append([InlineKeyboardButton("« Volver", callback_data='menu_habits')])
reply_markup = InlineKeyboardMarkup(keyboard)

await query.edit_message_text(
    "Selecciona el habito que completaste hoy:",
    reply_markup=reply_markup
)
```

async def habit_streaks(update: Update, context: ContextTypes.DEFAULT_TYPE):
“”“Mostrar rachas de habitos”””
query = update.callback_query
await query.answer()

```
user_id = query.from_user.id
conn = sqlite3.connect('productivity.db')
c = conn.cursor()

c.execute('SELECT id, habit_name FROM habits WHERE user_id = ?', (user_id,))
habits = c.fetchall()

if not habits:
    text = "📭 No tienes habitos registrados."
else:
    text = "🔥 *Tus Rachas:*\n\n"
    for habit in habits:
        # Calcular racha
        c.execute('''SELECT DATE(logged_at) FROM habit_logs 
                    WHERE habit_id = ? AND user_id = ?
                    ORDER BY logged_at DESC LIMIT 30''', (habit[0], user_id))
        dates = [row[0] for row in c.fetchall()]
        
        streak = 0
        if dates:
            current_date = datetime.now().date()
            for i in range(30):
                check_date = (current_date - timedelta(days=i)).strftime('%Y-%m-%d')
                if check_date in dates:
                    streak += 1
                else:
                    break
        
        text += f"▫️ *{habit[1]}*: {streak} dias 🔥\n"

conn.close()

keyboard = [[InlineKeyboardButton("« Volver", callback_data='menu_habits')]]
reply_markup = InlineKeyboardMarkup(keyboard)

await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
```

# ============================================

# POMODORO

# ============================================

async def menu_pomodoro(update: Update, context: ContextTypes.DEFAULT_TYPE):
“”“Menu Pomodoro”””
query = update.callback_query
await query.answer()

```
keyboard = [
    [InlineKeyboardButton("🍅 25 min", callback_data='pomo_25')],
    [InlineKeyboardButton("⏱ 15 min", callback_data='pomo_15')],
    [InlineKeyboardButton("⏱ 45 min", callback_data='pomo_45')],
    [InlineKeyboardButton("📊 Mis Sesiones", callback_data='pomo_stats')],
    [InlineKeyboardButton("« Volver", callback_data='back_main')]
]
reply_markup = InlineKeyboardMarkup(keyboard)

await query.edit_message_text(
    "🍅 *Pomodoro Timer*\n\nSelecciona la duracion de tu sesion:",
    reply_markup=reply_markup,
    parse_mode='Markdown'
)
```

async def start_pomodoro(update: Update, context: ContextTypes.DEFAULT_TYPE, duration: int):
“”“Iniciar sesion Pomodoro”””
query = update.callback_query
await query.answer()

```
context.user_data['waiting_for'] = f'pomo_task_{duration}'
await query.edit_message_text(
    f"🍅 Sesion de {duration} minutos\n\n✍️ ¿En que vas a trabajar?\n\n(Escribe /cancelar para cancelar)"
)
```

async def pomodoro_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
“”“Estadisticas de Pomodoro”””
query = update.callback_query
await query.answer()

```
user_id = query.from_user.id
conn = sqlite3.connect('productivity.db')
c = conn.cursor()

# Total de sesiones
c.execute('SELECT COUNT(*), SUM(duration) FROM pomodoro WHERE user_id = ?', (user_id,))
total_sessions, total_minutes = c.fetchone()

# Sesiones de hoy
c.execute('''SELECT COUNT(*), SUM(duration) FROM pomodoro 
             WHERE user_id = ? AND DATE(completed_at) = DATE('now')''', (user_id,))
today_sessions, today_minutes = c.fetchone()

conn.close()

total_minutes = total_minutes or 0
today_minutes = today_minutes or 0
total_hours = total_minutes / 60
today_hours = today_minutes / 60

text = f"""
```

📊 *Estadisticas Pomodoro*

*Hoy:*
🍅 Sesiones: {today_sessions or 0}
⏱ Tiempo: {today_hours:.1f} horas

*Total:*
🍅 Sesiones: {total_sessions or 0}
⏱ Tiempo: {total_hours:.1f} horas

¡Sigue asi! 💪
“””

```
keyboard = [[InlineKeyboardButton("« Volver", callback_data='menu_pomodoro')]]
reply_markup = InlineKeyboardMarkup(keyboard)

await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
```

# ============================================

# ESTADISTICAS

# ============================================

async def menu_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
“”“Menu de estadisticas”””
query = update.callback_query
await query.answer()

```
user_id = query.from_user.id

# Generar grafico
fig, axes = plt.subplots(2, 2, figsize=(12, 10))
fig.suptitle('📊 Estadisticas de Productividad', fontsize=16, fontweight='bold')

conn = sqlite3.connect('productivity.db')
c = conn.cursor()

# 1. Tareas completadas por dia (ultimos 7 dias)
c.execute('''SELECT DATE(completed_at) as date, COUNT(*) 
             FROM tasks 
             WHERE user_id = ? AND completed = 1 AND completed_at >= DATE('now', '-7 days')
             GROUP BY date
             ORDER BY date''', (user_id,))
task_data = c.fetchall()

if task_data:
    dates = [row[0] for row in task_data]
    counts = [row[1] for row in task_data]
    axes[0, 0].bar(dates, counts, color='#4CAF50')
    axes[0, 0].set_title('Tareas Completadas (7 dias)')
    axes[0, 0].set_xlabel('Fecha')
    axes[0, 0].set_ylabel('Tareas')
    axes[0, 0].tick_params(axis='x', rotation=45)
else:
    axes[0, 0].text(0.5, 0.5, 'Sin datos', ha='center', va='center')
    axes[0, 0].set_title('Tareas Completadas (7 dias)')

# 2. Sesiones Pomodoro por dia
c.execute('''SELECT DATE(completed_at) as date, COUNT(*), SUM(duration) 
             FROM pomodoro 
             WHERE user_id = ? AND completed_at >= DATE('now', '-7 days')
             GROUP BY date
             ORDER BY date''', (user_id,))
pomo_data = c.fetchall()

if pomo_data:
    dates = [row[0] for row in pomo_data]
    minutes = [row[2] for row in pomo_data]
    axes[0, 1].bar(dates, minutes, color='#FF5722')
    axes[0, 1].set_title('Minutos Pomodoro (7 dias)')
    axes[0, 1].set_xlabel('Fecha')
    axes[0, 1].set_ylabel('Minutos')
    axes[0, 1].tick_params(axis='x', rotation=45)
else:
    axes[0, 1].text(0.5, 0.5, 'Sin datos', ha='center', va='center')
    axes[0, 1].set_title('Minutos Pomodoro (7 dias)')

# 3. Habitos - Racha actual
c.execute('SELECT id, habit_name FROM habits WHERE user_id = ?', (user_id,))
habits = c.fetchall()

if habits:
    habit_names = []
    streaks = []
    for habit in habits:
        c.execute('''SELECT DATE(logged_at) FROM habit_logs 
                    WHERE habit_id = ? AND user_id = ?
                    ORDER BY logged_at DESC LIMIT 30''', (habit[0], user_id))
        dates = [row[0] for row in c.fetchall()]
        
        streak = 0
        if dates:
            current_date = datetime.now().date()
            for i in range(30):
                check_date = (current_date - timedelta(days=i)).strftime('%Y-%m-%d')
                if check_date in dates:
                    streak += 1
                else:
                    break
        
        habit_names.append(habit[1][:15])
        streaks.append(streak)
    
    axes[1, 0].barh(habit_names, streaks, color='#2196F3')
    axes[1, 0].set_title('Rachas de Habitos (dias)')
    axes[1, 0].set_xlabel('Dias')
else:
    axes[1, 0].text(0.5, 0.5, 'Sin datos', ha='center', va='center')
    axes[1, 0].set_title('Rachas de Habitos')

# 4. Resumen general
c.execute('SELECT COUNT(*) FROM tasks WHERE user_id = ? AND completed = 1', (user_id,))
total_tasks = c.fetchone()[0]

c.execute('SELECT COUNT(*) FROM pomodoro WHERE user_id = ?', (user_id,))
total_pomodoros = c.fetchone()[0]

c.execute('SELECT COUNT(*) FROM habits WHERE user_id = ?', (user_id,))
total_habits = c.fetchone()[0]

conn.close()

summary = f"""
Resumen Total:

✅ Tareas completadas: {total_tasks}
🍅 Sesiones Pomodoro: {total_pomodoros}
🎯 Habitos activos: {total_habits}

¡Sigue asi! 💪
"""

axes[1, 1].text(0.1, 0.5, summary, fontsize=12, verticalalignment='center')
axes[1, 1].axis('off')

plt.tight_layout()

# Guardar grafico
buf = io.BytesIO()
plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
buf.seek(0)
plt.close()

# Enviar grafico
await query.message.reply_photo(photo=buf, caption="📊 *Tus estadisticas de productividad*", parse_mode='Markdown')

keyboard = [[InlineKeyboardButton("« Volver", callback_data='back_main')]]
reply_markup = InlineKeyboardMarkup(keyboard)
await query.message.reply_text("Selecciona una opcion:", reply_markup=reply_markup)
```

# ============================================

# MANEJADORES DE CALLBACKS

# ============================================

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
“”“Manejar todos los callbacks de botones”””
query = update.callback_query
data = query.data

```
if data == 'back_main':
    await start(update, context)
elif data == 'menu_tasks':
    await menu_tasks(update, context)
elif data == 'menu_habits':
    await menu_habits(update, context)
elif data == 'menu_pomodoro':
    await menu_pomodoro(update, context)
elif data == 'menu_stats':
    await menu_stats(update, context)
elif data == 'task_new':
    await task_new(update, context)
elif data == 'task_list':
    await task_list(update, context)
elif data == 'task_complete':
    await task_complete(update, context)
elif data == 'task_delete':
    await task_delete(update, context)
elif data == 'habit_new':
    await habit_new(update, context)
elif data == 'habit_list':
    await habit_list(update, context)
elif data == 'habit_log':
    await habit_log(update, context)
elif data == 'habit_streaks':
    await habit_streaks(update, context)
elif data.startswith('pomo_'):
    duration = int(data.split('_')[1])
    await start_pomodoro(update, context, duration)
elif data == 'pomo_stats':
    await pomodoro_stats(update, context)
elif data.startswith('complete_'):
    task_id = int(data.split('_')[1])
    await complete_task(update, context, task_id)
elif data.startswith('delete_'):
    task_id = int(data.split('_')[1])
    await delete_task(update, context, task_id)
elif data.startswith('log_'):
    habit_id = int(data.split('_')[1])
    await log_habit(update, context, habit_id)
elif data == 'help':
    await help_command(update, context)
```

async def complete_task(update: Update, context: ContextTypes.DEFAULT_TYPE, task_id: int):
“”“Marcar tarea como completada”””
query = update.callback_query
await query.answer(“✅ ¡Tarea completada!”)

```
conn = sqlite3.connect('productivity.db')
c = conn.cursor()
c.execute('''UPDATE tasks SET completed = 1, completed_at = CURRENT_TIMESTAMP 
             WHERE id = ?''', (task_id,))
conn.commit()
conn.close()

await task_list(update, context)
```

async def delete_task(update: Update, context: ContextTypes.DEFAULT_TYPE, task_id: int):
“”“Eliminar tarea”””
query = update.callback_query
await query.answer(“🗑 Tarea eliminada”)

```
conn = sqlite3.connect('productivity.db')
c = conn.cursor()
c.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
conn.commit()
conn.close()

await task_list(update, context)
```

async def log_habit(update: Update, context: ContextTypes.DEFAULT_TYPE, habit_id: int):
“”“Registrar habito del dia”””
query = update.callback_query
user_id = query.from_user.id

```
conn = sqlite3.connect('productivity.db')
c = conn.cursor()

# Verificar si ya fue registrado hoy
c.execute('''SELECT id FROM habit_logs 
             WHERE habit_id = ? AND user_id = ? AND DATE(logged_at) = DATE('now')''', 
          (habit_id, user_id))

if c.fetchone():
    await query.answer("⚠️ Ya registraste este habito hoy", show_alert=True)
else:
    c.execute('INSERT INTO habit_logs (habit_id, user_id) VALUES (?, ?)', (habit_id, user_id))
    conn.commit()
    await query.answer("✅ ¡Habito registrado! 🔥")

conn.close()
await habit_streaks(update, context)
```

# ============================================

# MANEJO DE MENSAJES

# ============================================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
“”“Manejar mensajes de texto del usuario”””
user_id = update.message.from_user.id
text = update.message.text

```
if 'waiting_for' not in context.user_data:
    await update.message.reply_text("Usa /start para ver el menu principal")
    return

waiting_for = context.user_data['waiting_for']

# Nueva tarea
if waiting_for == 'new_task':
    conn = sqlite3.connect('productivity.db')
    c = conn.cursor()
    c.execute('INSERT INTO tasks (user_id, task) VALUES (?, ?)', (user_id, text))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(f"✅ Tarea agregada: *{text}*", parse_mode='Markdown')
    del context.user_data['waiting_for']
    await update.message.reply_text("Usa /start para volver al menu")

# Nuevo habito
elif waiting_for == 'new_habit':
    conn = sqlite3.connect('productivity.db')
    c = conn.cursor()
    c.execute('INSERT INTO habits (user_id, habit_name) VALUES (?, ?)', (user_id, text))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(f"✅ Habito creado: *{text}*", parse_mode='Markdown')
    del context.user_data['waiting_for']
    await update.message.reply_text("Usa /start para volver al menu")

# Tarea de Pomodoro
elif waiting_for.startswith('pomo_task_'):
    duration = int(waiting_for.split('_')[2])
    
    conn = sqlite3.connect('productivity.db')
    c = conn.cursor()
    c.execute('INSERT INTO pomodoro (user_id, duration, task_name) VALUES (?, ?, ?)', 
              (user_id, duration, text))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(
        f"🍅 *Sesion de {duration} minutos iniciada*\n\n"
        f"Tarea: _{text}_\n\n"
        f"⏰ Te avisare cuando termine.\n"
        f"¡Concentrate! 💪",
        parse_mode='Markdown'
    )
    
    # Programar recordatorio
    context.job_queue.run_once(
        pomodoro_complete,
        duration * 60,
        data={'user_id': user_id, 'task': text, 'duration': duration},
        chat_id=update.message.chat_id
    )
    
    del context.user_data['waiting_for']
```

async def pomodoro_complete(context: ContextTypes.DEFAULT_TYPE):
“”“Notificar cuando termina el Pomodoro”””
job = context.job
await context.bot.send_message(
chat_id=job.chat_id,
text=f”🎉 *¡Pomodoro completado!*\n\n”
f”Tarea: *{job.data[‘task’]}*\n”
f”Duracion: {job.data[‘duration’]} minutos\n\n”
f”¡Toma un descanso! ☕”,
parse_mode=‘Markdown’
)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
“”“Comando de ayuda”””
help_text = “””
❓ *Ayuda - Bot de Productividad*

*Comandos disponibles:*
/start - Menu principal
/cancelar - Cancelar operacion actual

*Funcionalidades:*

📝 *Tareas*

- Crea, completa y elimina tareas
- Visualiza pendientes y completadas

🎯 *Habitos*

- Registra habitos diarios
- Sigue tu racha de dias consecutivos

🍅 *Pomodoro*

- Sesiones de 15, 25 o 45 minutos
- Temporizador automatico
- Estadisticas de productividad

📊 *Estadisticas*

- Graficos de progreso
- Resumen de actividades
- Analisis de tendencias

¡Usa /start para comenzar! 🚀
“””

```
if update.callback_query:
    keyboard = [[InlineKeyboardButton("« Volver", callback_data='back_main')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(help_text, reply_markup=reply_markup, parse_mode='Markdown')
else:
    await update.message.reply_text(help_text, parse_mode='Markdown')
```

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
“”“Cancelar operacion actual”””
if ‘waiting_for’ in context.user_data:
del context.user_data[‘waiting_for’]
await update.message.reply_text(“❌ Operacion cancelada. Usa /start para volver al menu.”)
else:
await update.message.reply_text(“No hay nada que cancelar. Usa /start para ver el menu.”)

# ============================================

# MAIN

# ============================================

def main():
“”“Funcion principal”””
# Inicializar base de datos
init_db()

```
# IMPORTANTE: Reemplaza 'TU_TOKEN_AQUI' con tu token de BotFather
TOKEN = 'TU_TOKEN_AQUI'

# Crear aplicacion
application = Application.builder().token(TOKEN).build()

# Handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("cancelar", cancel))
application.add_handler(CallbackQueryHandler(button_callback))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Iniciar bot
print("🤖 Bot iniciado...")
application.run_polling(allowed_updates=Update.ALL_TYPES)
```

if **name** == ‘**main**’:
main()

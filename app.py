from flask import Flask, render_template, request, session, redirect, url_for
import csv
import os
import sys
import re

app = Flask(__name__)
app.secret_key = 'infuse12345678999999avb'  


CSV_FILE = 'tasks.csv'

def parse_level_from_tags(tags):
    for tag in tags:
        m = re.search(r'Lv\.(\d+)', tag)
        if m:
            return int(m.group(1))
    return 0

def load_tasks():
    tasks = []
    with open(CSV_FILE, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        for idx, row in enumerate(reader):
            img_path = row['图片']
            if 'static/images' in img_path:
                img_path = img_path.split('static/images')[-1].lstrip('/\\')
                img_path = 'images/' + img_path
            tags = row['标签'].split()
            lv = parse_level_from_tags(tags)
            tasks.append({
                'id': idx,
                'name': row['任务名'],
                'objective': row['目标'],
                'tags': tags,
                'level': lv,
                'image': img_path
            })
    return tasks

@app.route('/')
def index():
    tags_param = request.args.get('tags', '')
    selected_tags = [t for t in tags_param.split(',') if t]

    min_lv = request.args.get('min_lv', '')
    max_lv = request.args.get('max_lv', '')

    try:
        min_lv_val = int(min_lv)
    except:
        min_lv_val = None

    try:
        max_lv_val = int(max_lv)
    except:
        max_lv_val = None

    tasks = load_tasks()
    completed = session.get('completed_tasks', [])

    def task_matches(task): 
        if selected_tags:
            # 这里过滤掉 selected_tags 中带 Lv. 的标签，避免匹配时考虑它们
            filtered_selected_tags = [tag for tag in selected_tags if not tag.startswith('Lv.')]
            if not all(tag in task['tags'] for tag in filtered_selected_tags):
                return False
        lv = task['level']
        if min_lv_val is not None and lv < min_lv_val:
            return False
        if max_lv_val is not None and lv > max_lv_val:
            return False
        return True

    filtered_tasks = [task for task in tasks if task_matches(task)]

    tag_stats = {}
    for task in tasks:
        for tag in task['tags']:
            # 跳过以 Lv. 开头的标签
            if tag.startswith('Lv.'):
                continue
            tag_stats.setdefault(tag, {'total': 0, 'completed': 0})
            tag_stats[tag]['total'] += 1
            if task['id'] in completed:
                tag_stats[tag]['completed'] += 1

    return render_template('index.html',
                        tasks=filtered_tasks,
                        completed=completed,
                        tag_stats=tag_stats,
                        selected_tags=selected_tags,
                        min_lv=min_lv,
                        max_lv=max_lv)


@app.route('/toggle/<int:task_id>')
def toggle(task_id):
    completed = session.get('completed_tasks', [])
    if task_id in completed:
        completed.remove(task_id)
    else:
        completed.append(task_id)
    session['completed_tasks'] = completed
    return redirect(request.referrer or url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)

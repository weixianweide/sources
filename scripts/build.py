#!/usr/bin/env python3
"""检查 sources/ 下的数据源, 并按 order.txt 的顺序拼成 subscription.json.

    python3 scripts/build.py                     检查并重新生成 subscription.json
    python3 scripts/build.py --check [文件 ...]  只检查不写文件; 列出的文件 (PR 改到的) 额外提示需要维护者留意的地方

每个 sources/*.json 是一个数据源, 即应用数据源设置里「导出」出来的那一段:
{"factoryId": "...", "version": 1, "arguments": {"name": "...", ...}}
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES_DIR = os.path.join(ROOT, 'sources')
ORDER_FILE = os.path.join(ROOT, 'order.txt')
OUTPUT = os.path.join(ROOT, 'subscription.json')

FILE_NAME = re.compile(r'^[a-z0-9][a-z0-9-]*\.json$')
# 应用认得的数据源类型
KNOWN_TYPES = {'web-selector', 'rule', 'maccms', 'direct-api', 'rss', 'cloud-drive', 'cloud-drive-share-search'}
# 网盘的接入方式只由维护者改
MAINTAINER_TYPES = {'cloud-drive', 'cloud-drive-share-search'}

errors = []
notes = []


def error(file, message):
    errors.append('%s: %s' % (file, message))


def load(file):
    path = os.path.join(SOURCES_DIR, file)
    if not FILE_NAME.match(file):
        error(file, '文件名只能用小写字母、数字和 -, 以 .json 结尾')
    try:
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        error(file, '不是合法的 JSON (%s)' % e)
        return None
    if not isinstance(data, dict):
        error(file, '应当是一个对象 {"factoryId": ..., "version": ..., "arguments": {...}}')
        return None
    extra = set(data) - {'factoryId', 'version', 'arguments'}
    if extra:
        error(file, '多出了字段 %s' % ', '.join(sorted(extra)))
    if data.get('factoryId') not in KNOWN_TYPES:
        error(file, '不认得的类型 factoryId=%r (可用: %s)' % (data.get('factoryId'), ', '.join(sorted(KNOWN_TYPES))))
    if not isinstance(data.get('version'), int) or isinstance(data.get('version'), bool) or data['version'] < 1:
        error(file, 'version 应当是正整数')
    arguments = data.get('arguments')
    if not isinstance(arguments, dict):
        error(file, 'arguments 应当是一个对象')
        return None
    if not isinstance(arguments.get('name'), str) or not arguments['name'].strip():
        error(file, 'arguments.name (数据源名称) 不能为空')
    return data


def main():
    args = sys.argv[1:]
    check = bool(args) and args[0] == '--check'
    changed = {os.path.basename(a) for a in args[1:]} if check else set()

    files = sorted(f for f in os.listdir(SOURCES_DIR) if not f.startswith('.'))
    order = []
    with open(ORDER_FILE, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if line not in files:
                errors.append('order.txt: sources/%s 不存在' % line)
            elif line in order:
                errors.append('order.txt: %s 写了两次' % line)
            else:
                order.append(line)
    order += [f for f in files if f not in order]

    sources, names = [], {}
    for file in order:
        data = load(file)
        if data is None:
            continue
        name = (data.get('arguments') or {}).get('name')
        if isinstance(name, str):
            if name in names:
                error(file, '数据源名称「%s」和 %s 重复' % (name, names[name]))
            names[name] = file
        if file in changed:
            arguments = data.get('arguments') or {}
            if data.get('factoryId') in MAINTAINER_TYPES:
                notes.append('%s: 网盘类数据源, 需要维护者确认' % file)
            if 'tier' in arguments or 'channelTiers' in arguments:
                notes.append('%s: 写了层级 (tier / channelTiers), 层级由维护者定' % file)
        sources.append(data)

    for e in errors:
        print('::error::' + e)
    for n in notes:
        print('::warning::' + n)
    if errors:
        print('检查没通过: %d 处问题' % len(errors))
        return 1
    print('检查通过: %d 个数据源' % len(sources))
    for file in sorted(changed):
        if file in names.values():
            print('  改到了 sources/%s' % file)
    if check:
        return 0
    text = json.dumps({'exportedMediaSourceDataList': {'mediaSources': sources}}, ensure_ascii=False, indent=2)
    with open(OUTPUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)
    print('已生成 subscription.json')
    return 0


if __name__ == '__main__':
    sys.exit(main())

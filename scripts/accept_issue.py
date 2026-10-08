#!/usr/bin/env python3
"""把「提交或更新数据源」issue 里的 JSON 写成 sources/ 下的文件 (维护者加「采纳」标签时由 Action 调用).

读环境变量 ISSUE_NUMBER / ISSUE_BODY (issue 表单生成的正文); 成功时往 GITHUB_OUTPUT 写 file / name / action,
失败时把原因写到 stderr 并以非零退出.
"""
import json
import os
import re
import sys
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES_DIR = os.path.join(ROOT, 'sources')


def fail(message):
    print(message, file=sys.stderr)
    sys.exit(1)


def sections(body):
    """issue 表单的正文: 每个字段是「### 标题」加内容; 没填的是 _No response_."""
    parts = re.split(r'^###\s+(.+?)\s*$', body.replace('\r\n', '\n'), flags=re.M)
    result = {}
    for i in range(1, len(parts) - 1, 2):
        value = parts[i + 1].strip()
        result[parts[i].strip()] = '' if value == '_No response_' else value
    return result


def parse_source(text):
    text = text.strip()
    fence = re.match(r'^```[a-zA-Z]*\n(.*)\n```$', text, flags=re.S)
    if fence:
        text = fence.group(1)
    try:
        root = json.loads(text)
    except ValueError as e:
        fail('「数据源 JSON」不是合法的 JSON: %s' % e)
    # 认应用导出的几种形状: 单个源 / 数组 / {"mediaSources": [...]} / 整份订阅
    if isinstance(root, dict) and 'exportedMediaSourceDataList' in root:
        root = root['exportedMediaSourceDataList']
    if isinstance(root, dict) and 'mediaSources' in root:
        root = root['mediaSources']
    items = root if isinstance(root, list) else [root]
    if len(items) != 1:
        fail('「数据源 JSON」里有 %d 个数据源, 一个 issue 只提交一个' % len(items))
    source = items[0]
    if not isinstance(source, dict) or not isinstance(source.get('arguments'), dict):
        fail('「数据源 JSON」应当是应用里「导出」出来的那一段 ({"factoryId": ..., "version": ..., "arguments": {...}})')
    return source


def existing_sources():
    result = {}
    for file in sorted(os.listdir(SOURCES_DIR)):
        if file.endswith('.json'):
            with open(os.path.join(SOURCES_DIR, file), encoding='utf-8') as f:
                result[file] = json.load(f)
    return result


def slug_of(url):
    host = urlparse(url).hostname or ''
    host = re.sub(r'^www\.', '', host.lower())
    return re.sub(r'[^a-z0-9]+', '-', host).strip('-')


def main():
    number = os.environ['ISSUE_NUMBER']
    fields = sections(os.environ['ISSUE_BODY'])
    if '数据源 JSON' not in fields:
        fail('没找到「数据源 JSON」, 请用「提交或更新数据源」表单提交')
    source = parse_source(fields['数据源 JSON'])
    name = source['arguments'].get('name') or ''
    named = fields.get('数据源名称', '')
    existing = existing_sources()
    by_name = {data.get('arguments', {}).get('name'): file for file, data in existing.items()}

    if fields.get('类型', '').startswith('更新'):
        file = by_name.get(named) or by_name.get(name)
        if not file:
            fail('订阅里没有名叫「%s」的数据源, 新的源请选「新增数据源」' % (named or name))
        action = 'update'
    else:
        if name in by_name:
            fail('订阅里已经有「%s」(sources/%s), 要更新请选「更新已有的数据源」' % (name, by_name[name]))
        urls = [fields.get('网站地址', '')] + re.findall(r'https?://[^\s"\'\\]+', json.dumps(source, ensure_ascii=False))
        slug = next((s for s in map(slug_of, urls) if s), '') or 'issue-%s' % number
        file, n = slug + '.json', 2
        while file in existing:
            file, n = '%s-%d.json' % (slug, n), n + 1
        action = 'add'

    with open(os.path.join(SOURCES_DIR, file), 'w', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(source, ensure_ascii=False, indent=2) + '\n')
    with open(os.environ.get('GITHUB_OUTPUT', os.devnull), 'a', encoding='utf-8') as out:
        out.write('file=%s\nname=%s\naction=%s\n' % (file, name, action))
    print('%s sources/%s (%s)' % ('更新' if action == 'update' else '新增', file, name))


if __name__ == '__main__':
    main()

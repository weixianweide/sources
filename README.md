# sources

数据源订阅。订阅地址用 `subscription.json` 的 raw 链接：

```
https://raw.githubusercontent.com/weixianweide/sources/main/subscription.json
```

## 加数据源

欢迎加数据源，或者更新已经失效的源。

- **不用 git**：开一个「[提交或更新数据源](../../issues/new?template=source.yml)」的 issue，按表单填，把应用数据源设置里「导出」的内容贴进去。
- **用 git**：在 `sources/` 下加一个文件（一个源一个文件，文件名只用小写字母、数字和 `-`），提 PR。PR 会自动检查格式。

维护者测过之后合并。层级（`tier`、`channelTiers`，决定优先选哪个源）由维护者定，提交时不用写。

提交的配置要是你自己写的，或者原作者的许可允许转载；没有许可证的规则库里的规则不能提交。网站不能需要付费或登录。

## 目录

- `sources/*.json`：每个文件是一个数据源，即应用里「导出」出来的那一段
- `order.txt`：排在订阅最前面的源；没写在里面的按文件名排在后面
- `scripts/build.py`：检查 `sources/` 并生成 `subscription.json`（本地运行：`python3 scripts/build.py`）
- `subscription.json`：合并到 main 后自动生成，不要直接改

## 许可

本仓库的内容以 [CC0 1.0](LICENSE) 发布，投稿也按同一许可证接收。

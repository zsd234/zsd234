# GitHub 上传指南

## 方法一：网页上传

1. 打开 GitHub。
2. 新建仓库，例如 `ppt-template-deck-builder`。
3. 选择 `Add file` -> `Upload files`。
4. 把本文件所在的整个文件夹内容拖进去。
5. 点击 `Commit changes`。

完成后，仓库里应该能看到：

- `README.md`
- `requirements.txt`
- `scripts/`
- `examples/`
- `skills/ppt-template-deck-builder/`

## 方法二：命令行上传

在这个目录打开 PowerShell：

```powershell
git init
git add .
git commit -m "Add ppt template deck builder skill"
git branch -M main
git remote add origin https://github.com/<你的用户名>/<你的仓库名>.git
git push -u origin main
```

把 `<你的用户名>` 和 `<你的仓库名>` 换成你自己的。

## 上传后怎么用

下载或克隆仓库后运行：

```powershell
.\scripts\install.ps1
```

然后在 Codex 里调用：

```text
使用 $ppt-template-deck-builder，按这个模板和我的文档生成 PPT。
```

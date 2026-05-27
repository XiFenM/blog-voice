# 表格导入 使用说明

# 功能背景：

墨墨记忆卡 的用户们，有时会反馈说：我已经有了一个表格，里面是规整的内容，例如：

- 第一列单词、第二列释义

- 第一列名词、第二列解释

- 第一列题目、第二列答案

我们开发了表格导入功能，方便大家对已有内容进行**快速的****、****统一样式的**批量制卡

# 功能入口：

> 打开一个你自己的原创牌组，右上角有「表格导入」
> 
> 

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=OWFmYzY4NjQ4NDc3MTBlNzVjMWY4MDRlOGZiNGUyOTVfMjVlNGNhZDQ3N2JhYjI0ZTk3OGU2YmRkNzNjYTY5ZmNfSUQ6NzIzMTEzNTUxNDYzOTkyNTI1MV8xNzc5ODYyNDE5OjE3Nzk5NDg4MTlfVjM)

# 使用说明：

1. 在这个区域可以像手机一样输入语法，控制卡片的样式，语法参考：[Markji 2\.0 使用说明](https://maimemo.feishu.cn/docs/doccnjbGpf4ke3sU9U9jsuphwKE)



![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=YjFkZDVlN2E2MTE3ZmE2NTNhYTQ1NjJjZjY0Mzg4ZDRfYmNjNGM1OWVmOTRlYmIzYjAxMzBiY2U5NjQyNGFjNDNfSUQ6NzIzMDk4NzUwNjg1MzAzNjAzNl8xNzc5ODYyNDE5OjE3Nzk5NDg4MTlfVjM)



2. 对于你想用「表格的列」替换的「字段」，只需要在语法中用`\{\{\}\}`包裹起来，被包裹的字段我们会为你标绿，并在下方的表格预览区预览。



![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MDY2NjVkNjJjMDRmODY0MDMxNTk5OWZlYTUxNTAyODVfYTEzZTE3MTFmZDYzMGZmYzRkMmY4MjMwZDM5MjA3OGVfSUQ6NzIzMTEzNTA3OTUzNTAwMTYwNF8xNzc5ODYyNDE5OjE3Nzk5NDg4MTlfVjM)

3. 样式模板制作好后，下载表格，放入内容，上传表格，之后我们会把你表格填入页面进行预览确认

    1. 此时你仍然可以修改左侧的模板，但修改后需要重新上传文件

    2. 确认真实内容预览无误，则开始真正的导入

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NzA3OTcyMDhiM2EzNGUzZmUwMTE4MWVlNmM1YWE4YzlfZTI1NzY5MzYxNTVlZDc0YzE5NjgxMTg2N2NlZmU4MDBfSUQ6NzIzMTEzNDkwNzI2MTgxMjc0MF8xNzc5ODYyNDE5OjE3Nzk5NDg4MTlfVjM)

4. 导入结束后开始查看效果



![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=YjMzMjlkNDdkYTJlYzZiOTk0MzcxZTdlMzZhYjUwOTlfNTdmMmNjNTczNzdkOGMwODUwMjAzNTIyZDZmZjYzODhfSUQ6NzIzMTEzNTI2NzE1MDYyNjgyMF8xNzc5ODYyNDE5OjE3Nzk5NDg4MTlfVjM)

# 推荐模板

> 语法文档：[Markji 2\.0 使用说明](https://maimemo.feishu.cn/docs/doccnjbGpf4ke3sU9U9jsuphwKE)
> 
> 

## 问答题：

> 只用到了“答案线”语法
> 
> 最简单的形式，但也是学习效果最好的卡片，它是一个完美的原子化知识，你或者其他人学习来都会很舒服
> 
> 

```JSON
{{问题}}
---
{{答案}}
```

## 概念卡：

> 如果你想记忆什么是“西瓜”，正面一个大大的“西瓜”，反面是解释，非常舒服
> 
> 

用到了“答案线”、“整行样式”语法

```JSON
[P#H1#{{概念}}]
---
{{定义}}
```

如果想**居中**显示可加上 center 参数

```JSON
[P#H1,center#{{概念}}]
---
{{定义}}
```

如果想显示**墨墨绿**可以套上文字颜色

```JSON
[P#H1,center#[T#!36b59d#{{概念}}]]
---
{{定义}}
```

## 选择题

> 用到了指定答案的“选择题”语法，答案的格式为：ABC、abc
> 
> 解析放在答案线的后面，确保用户做题后才出现解析
> 
> 

```JSON
{{问题描述}}
[Choice#ans/{{答案}}#
- {{A 选项}}
- {{B 选项}}
- {{C 选项}}
- {{D 选项}}
]
---
解析：{{解析}}
```

## 其他模板：

> 我很期待大家是怎么用这个功能的，以及对于批量导入的建议，欢迎在文档里评论留言
> 
> 









# 更多帮助文档：

[Markji 帮助文档索引](https://xefmb40b8l.feishu.cn/docx/doxcnkxpR2GA8Nrn3r0ApzkYmgM) 


# 清华教师评价 Demo

这是一个可直接运行的前端 demo，按 GUI 模块拆分代码：

- `modules/login`：登录与问题验证模块
- `modules/main`：学院分类与教师列表模块
- `modules/upload`：教师信息、评分、评语上传模块
- `modules/detail`：教师详情、全部评分与评语模块
- `modules/logs`：系统日志与开发者信息模块
- `services/storage.js`：用 localStorage 模拟后台数据访问
- `data/supabaseConfig.js`：Supabase 云端数据库配置
- `data/supabase-schema.sql`：Supabase 建表和试用版权限策略
- `data/authConfig.js`：验证问题与答案配置
- `data/seedData.js`：初始示例数据

## 运行方式

用浏览器打开 `index.html` 即可运行。

默认验证答案：`清华`、`Tsinghua` 或 `THU`。

## 云端数据库

推荐使用 Supabase。当前代码会优先连接 Supabase；如果没有填写配置或连接失败，会自动退回浏览器 localStorage。

1. 在 Supabase 创建新项目。
2. 打开 SQL Editor，运行 `data/supabase-schema.sql`。
3. 在 Project Settings -> API 中复制 Project URL 和 anon public key。
4. 填入 `data/supabaseConfig.js`：

```js
export const supabaseConfig = {
  url: "https://你的项目.supabase.co",
  anonKey: "你的 anon public key"
};
```

5. 提交并推送到 GitHub Pages。

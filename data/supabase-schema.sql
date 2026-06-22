create table if not exists teachers (
  id text primary key,
  name text not null,
  college text not null,
  title text not null default '待补充',
  email text not null default '待补充',
  research text not null default '待补充',
  intro text not null default '暂无介绍',
  created_at timestamptz not null default now()
);

create table if not exists reviews (
  id bigint generated always as identity primary key,
  teacher_id text not null references teachers(id) on delete cascade,
  score numeric not null check (score >= 1 and score <= 5),
  text text not null,
  author text not null default '匿名学生',
  date date not null default current_date,
  created_at timestamptz not null default now()
);

create table if not exists system_logs (
  id bigint generated always as identity primary key,
  time text not null,
  message text not null,
  created_at timestamptz not null default now()
);

insert into teachers (id, name, college, title, email, research, intro)
values
  ('t-automation-chen', '陈教授', '自动化系', '教授', 'chen@example.tsinghua.edu.cn', '智能控制、机器学习与系统建模', '课程结构清晰，重视基础推导和工程实践。'),
  ('t-cs-li', '李教授', '计算机科学与技术系', '副教授', 'li@example.tsinghua.edu.cn', '数据库系统、数据管理与云计算', '课堂案例丰富，适合想做系统方向的同学。'),
  ('t-ee-wang', '王教授', '电子工程系', '教授', 'wang@example.tsinghua.edu.cn', '信号处理、通信系统与智能感知', '理论要求高，课堂板书细致。')
on conflict (id) do nothing;

insert into reviews (teacher_id, score, text, author, date)
values
  ('t-automation-chen', 4.7, '讲课节奏稳定，作业有挑战但反馈及时。', '匿名学生', '2026-06-20'),
  ('t-cs-li', 4.4, '项目训练很实用，期末复习范围明确。', '匿名学生', '2026-06-19'),
  ('t-ee-wang', 4.2, '考试偏重理解，建议认真跟每周习题。', '匿名学生', '2026-06-18');

insert into system_logs (time, message)
values
  ('2026-06-22 09:00', 'Supabase 云端数据库初始化完成。'),
  ('2026-06-22 09:05', '教师、评价和系统日志表已创建。');

alter table teachers enable row level security;
alter table reviews enable row level security;
alter table system_logs enable row level security;

drop policy if exists "public read teachers" on teachers;
drop policy if exists "public insert teachers" on teachers;
drop policy if exists "public read reviews" on reviews;
drop policy if exists "public insert reviews" on reviews;
drop policy if exists "public read logs" on system_logs;
drop policy if exists "public insert logs" on system_logs;

create policy "public read teachers" on teachers for select using (true);
create policy "public insert teachers" on teachers for insert with check (true);

create policy "public read reviews" on reviews for select using (true);
create policy "public insert reviews" on reviews for insert with check (true);

create policy "public read logs" on system_logs for select using (true);
create policy "public insert logs" on system_logs for insert with check (true);

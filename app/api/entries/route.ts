import { env } from "cloudflare:workers";
import { headers } from 'next/headers';

async function ensureTable() {
  if (!env.DB) throw new Error('Database unavailable');
}

export async function GET() {
  const owner=(await headers()).get('oai-authenticated-user-id');
  if(!owner)return Response.json([]);
  await ensureTable();
  const result = await env.DB.prepare(
    "SELECT id, name, excerpt, notes, created_at FROM custom_entries WHERE owner=? ORDER BY id DESC LIMIT 100"
  ).bind(owner).all();
  return Response.json(result.results ?? []);
}

export async function POST(request: Request) {
  if (!(await headers()).get('oai-authenticated-user-id')) return Response.json({error:'请先登录'},{status:401});
  if (request.headers.get('origin') !== new URL(request.url).origin) return Response.json({error:'请求来源不符'},{status:403});
  await ensureTable();
  const body = (await request.json()) as { name?: string; excerpt?: string; notes?: string };
  const name = body.name?.trim();
  const excerpt = body.excerpt?.trim();
  if (!name || !excerpt) {
    return Response.json({ error: "香名和原文不能为空" }, { status: 400 });
  }
  const result = await env.DB.prepare(
    "INSERT INTO custom_entries (name, excerpt, notes, owner) VALUES (?, ?, ?, ?) RETURNING id, name, excerpt, notes, created_at"
  ).bind(name.slice(0, 120), excerpt.slice(0, 2000), (body.notes ?? "").slice(0, 2000),(await headers()).get('oai-authenticated-user-id')).first();
  return Response.json(result, { status: 201 });
}

import {database} from '../../../db/binding';
import {reconstruct,modelVersion} from '../../research-engine';
import {headers} from 'next/headers';
export const dynamic='force-dynamic';
export async function GET(){
  try{
    const user=(await headers()).get('oai-authenticated-user-id')||'';
    const data=await database().prepare('SELECT id,title,source,notes,observed,result,model_version,published,created_at FROM restorations WHERE published=1 OR owner=? ORDER BY created_at DESC LIMIT 200').bind(user).all();
    return Response.json({records:data.results,signedIn:!!user});
  }catch(error){console.error('restoration_read',error);return Response.json({error:'资料库暂时无法连接，请稍后重试。'},{status:503});}
}
export async function POST(request:Request){
  const h=await headers();const user=h.get('oai-authenticated-user-id');
  if(!user)return Response.json({error:'登录后可以保存香方。'},{status:401});
  const origin=request.headers.get('origin');
  if(!origin||new URL(origin).host!==new URL(request.url).host)return Response.json({error:'请求来源不符。'},{status:403});
  if(Number(request.headers.get('content-length')||0)>16000)return Response.json({error:'内容过长。'},{status:413});
  try{
    const text=await request.text();if(text.length>16000)return Response.json({error:'内容过长。'},{status:413});
    const body=JSON.parse(text);const title=String(body.title||'').trim();
    if(!title||title.length>120)return Response.json({error:'请填写不超过 120 字的香名。'},{status:400});
    if(!body.observed||typeof body.observed!=='object'||Array.isArray(body.observed))throw new Error('请填写已知香材。');
    const result=reconstruct(body.observed,body.totalCount,body.knownMass);
    const id=crypto.randomUUID();
    await database().prepare('INSERT INTO restorations (id,owner,title,source,notes,observed,result,model_version,published) VALUES (?,?,?,?,?,?,?,?,?)')
      .bind(id,user,title,String(body.source||'').slice(0,2000),String(body.notes||'').slice(0,4000),JSON.stringify(body.observed),JSON.stringify(result),modelVersion,body.published===true?1:0).run();
    return Response.json({id,result},{status:201});
  }catch(error){console.error('restoration_save',error);return Response.json({error:error instanceof SyntaxError?'提交内容格式错误。':'保存失败，请检查输入后重试；当前内容已保留。'},{status:400});}
}

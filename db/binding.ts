import {env} from 'cloudflare:workers';
export function database(){if(!env.DB)throw new Error('D1 database unavailable');return env.DB;}

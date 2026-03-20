import { serve } from 'https://deno.land/std@0.201.0/http/server.ts';
import { createClient } from 'npm:@supabase/supabase-js@2.28.0';

// Environment variables (provided by Supabase Edge runtime)
const SUPABASE_URL = Deno.env.get('SUPABASE_URL') || '';
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') || '';
// API key for function access (set via supabase secrets in production)
const FUNCTION_API_KEY = Deno.env.get('DATAPOINTS_API_KEY') || 'change-me';

if (!SUPABASE_URL || !SUPABASE_SERVICE_ROLE_KEY) {
  console.error('Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY');
}

const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, {
  global: { headers: { 'x-function': 'datapoints-api' } }
});

interface Datapoint {
  temperature: number;
  measured_at: string; // ISO
}

console.info('datapoints-api starting');

function unauthorized() {
  return new Response(JSON.stringify({ error: 'Unauthorized' }), { status: 401, headers: { 'Content-Type': 'application/json' } });
}

async function handlePost(req: Request) {
  const body = await req.json().catch(() => null);
  if (!body) return new Response(JSON.stringify({ error: 'Invalid JSON' }), { status: 400, headers: { 'Content-Type': 'application/json' } });

  const { temperature, measured_at } = body as Partial<Datapoint>;
  if (typeof temperature !== 'number' || !measured_at) return new Response(JSON.stringify({ error: 'Missing fields' }), { status: 400, headers: { 'Content-Type': 'application/json' } });

  const { data, error } = await supabase.from('datapoints').insert([{ temperature, measured_at }]);
  if (error) return new Response(JSON.stringify({ error: error.message }), { status: 500, headers: { 'Content-Type': 'application/json' } });

  return new Response(JSON.stringify({ success: true, data }), { status: 201, headers: { 'Content-Type': 'application/json' } });
}

async function handleGet(req: Request) {
  const header = req.headers.get('most-recent') || '1';
  const n = parseInt(header, 10);
  if (Number.isNaN(n) || n < 1) return new Response(JSON.stringify({ error: 'Invalid most-recent header' }), { status: 400, headers: { 'Content-Type': 'application/json' } });

  // Fetch most recent n datapoints ordered by timestamp desc
  const { data, error } = await supabase
    .from('datapoints')
    .select('temperature,measured_at')
    .order('measured_at', { ascending: false })
    .limit(n);
  if (error) return new Response(JSON.stringify({ error: error.message }), { status: 500, headers: { 'Content-Type': 'application/json' } });

  // Return in chronological order (oldest first) if multiple
  const result = (data || []).slice().reverse();
  return new Response(JSON.stringify({ data: result }), { status: 200, headers: { 'Content-Type': 'application/json' } });
}

serve(async (req: Request) => {
  const url = new URL(req.url);
  // Simple API key check
  const key = req.headers.get('x-api-key') || '';
  if (key !== FUNCTION_API_KEY) return unauthorized();

  if (req.method === 'POST' && url.pathname === '/datapoints-api') return handlePost(req);
  if (req.method === 'GET' && url.pathname === '/datapoints-api') return handleGet(req);

  return new Response(JSON.stringify({ error: 'Function not Found. Function path name was: ' + url.pathname }), { status: 404, headers: { 'Content-Type': 'application/json' } });
});

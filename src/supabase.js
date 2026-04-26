// src/supabase.js
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'https://xmgelmwoydbtcvltfbde.supabase.co'
const supabaseAnonKey = 'sb_publishable_h0xQm5Sq9Yydv-zs1pu5gA_6sqIfXUt'

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

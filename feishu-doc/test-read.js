const { getTenantAccessToken } = require('./lib/auth');

async function main() {
  const docToken = 'JvpHdyqtEo2lscx17UTcSZJkn3f';
  
  console.log('Getting access token...');
  const accessToken = await getTenantAccessToken();
  console.log('Token obtained:', accessToken.substring(0, 10) + '...');

  // Step 1: Try as wiki token first
  console.log('\n--- Trying Wiki Resolution ---');
  try {
    const wikiRes = await fetch(`https://open.feishu.cn/open-apis/wiki/v2/spaces/get_node?token=${docToken}`, {
      headers: { 'Authorization': `Bearer ${accessToken}` }
    });
    const wikiData = await wikiRes.json();
    console.log('Wiki result:', JSON.stringify(wikiData, null, 2));
  } catch(e) {
    console.log('Wiki resolution failed:', e.message);
  }

  // Step 2: Try reading as docx directly
  console.log('\n--- Trying Direct Docx Read ---');
  try {
    const rawRes = await fetch(`https://open.feishu.cn/open-apis/docx/v1/documents/${docToken}/raw_content`, {
      headers: { 'Authorization': `Bearer ${accessToken}` }
    });
    const rawData = await rawRes.json();
    console.log('Raw content result code:', rawData.code, rawData.msg);
    if (rawData.code === 0) {
      console.log('Content preview:', rawData.data?.content?.substring(0, 500));
    }
  } catch(e) {
    console.log('Direct read failed:', e.message);
  }

  // Step 3: Try getting doc info
  console.log('\n--- Trying Doc Info ---');
  try {
    const infoRes = await fetch(`https://open.feishu.cn/open-apis/docx/v1/documents/${docToken}`, {
      headers: { 'Authorization': `Bearer ${accessToken}` }
    });
    const infoData = await infoRes.json();
    console.log('Doc info:', JSON.stringify(infoData, null, 2));
  } catch(e) {
    console.log('Doc info failed:', e.message);
  }

  // Step 4: Try getting blocks
  console.log('\n--- Trying Blocks ---');
  try {
    const blocksRes = await fetch(`https://open.feishu.cn/open-apis/docx/v1/documents/${docToken}/blocks?page_size=500`, {
      headers: { 'Authorization': `Bearer ${accessToken}` }
    });
    const blocksData = await blocksRes.json();
    console.log('Blocks result code:', blocksData.code, blocksData.msg);
    if (blocksData.code === 0) {
      const items = blocksData.data?.items || [];
      console.log('Block count:', items.length);
      console.log('First 3 blocks:', JSON.stringify(items.slice(0, 3), null, 2));
    }
  } catch(e) {
    console.log('Blocks read failed:', e.message);
  }
}

main().catch(e => console.error('Fatal:', e));

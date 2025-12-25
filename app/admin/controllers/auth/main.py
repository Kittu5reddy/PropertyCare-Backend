from fastapi import APIRouter




admin_auth=APIRouter(prefix='/admin-auth',tags=['Admin Auth'])

@admin_auth.post('/login')
async def login():
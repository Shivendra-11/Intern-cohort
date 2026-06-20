import { Controller, Get, Post } from '@nestjs/common';

@Controller('transactions')
export class TransactionsController {
  @Get()
  findAll() {
    return [];
  }

  @Post()
  create() {
    return { ok: true };
  }
}

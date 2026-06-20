import { Injectable } from '@nestjs/common';

export interface Transaction {
  id: string;
  amount: number;
}

@Injectable()
export class TransactionsService {
  private items: Transaction[] = [];

  all(): Transaction[] {
    return this.items;
  }
}

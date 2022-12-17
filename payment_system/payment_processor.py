import time
from threading import Thread, Semaphore, Lock

from globals import *
from payment_system.bank import Bank
from utils.transaction import Transaction, TransactionStatus
from utils.logger import LOGGER
from utils.currency import get_exchange_rate


class PaymentProcessor(Thread):
    """
    Uma classe para representar um processador de pagamentos de um banco.
    Se você adicionar novos atributos ou métodos, lembre-se de atualizar essa docstring.

    ...

    Atributos
    ---------
    _id : int
        Identificador do processador de pagamentos.
    bank: Bank
        Banco sob o qual o processador de pagamentos operará.

    Métodos
    -------
    run():
        Inicia thread to PaymentProcessor
    process_transaction(transaction: Transaction) -> TransactionStatus:
        Processa uma transação bancária.
    """

    def __init__(self, _id: int, bank: Bank):
        Thread.__init__(self)
        self._id  = _id
        self.bank = bank


    def run(self):
        """
        Esse método deve buscar Transactions na fila de transações do banco e processá-las 
        utilizando o método self.process_transaction(self, transaction: Transaction).
        Ele não deve ser finalizado prematuramente (antes do banco realmente fechar).
        """
        # TODO: IMPLEMENTE/MODIFIQUE O CÓDIGO NECESSÁRIO ABAIXO !

        LOGGER.info(f"Inicializado o PaymentProcessor {self._id} do Banco {self.bank._id}!")
        queue = banks[self.bank._id].transaction_queue

        while self.bank.operating:
            try:
                self.bank.sem_queue.acquire() # semafaro pra bloquear outras threads
                self.bank.lock_transaction.acquire() # Proteção da região critica
                if not banks[self.bank._id].operating:
                    break
                transaction = queue.pop()
                self.bank.lock_transaction.release()
                # LOGGER.info(f"Transaction_queue do Banco {self.bank._id}: {len(queue)}")
            except Exception as err:
                LOGGER.error(f"Falha em PaymentProcessor.run(): {err}")
            else:
                self.process_transaction(transaction)
                LOGGER.info(f'Transação {transaction._id} do banco {self.bank._id} finalizada. ---- {transaction.status}')

        LOGGER.info(f"O PaymentProcessor {self._id} do banco {self.bank._id} foi finalizado.")


    def process_transaction(self, transaction: Transaction) -> TransactionStatus:
        """
        Esse método deverá processar as transações bancárias do banco ao qual foi designado.
        Caso a transferência seja realizada para um banco diferente (em moeda diferente), a 
        lógica para transações internacionais detalhada no enunciado (README.md) deverá ser
        aplicada.
        Ela deve retornar o status da transacão processada.
        """
        # TODO: IMPLEMENTE/MODIFIQUE O CÓDIGO NECESSÁRIO ABAIXO !

        LOGGER.info(f"PaymentProcessor {self._id} do Banco {self.bank._id} iniciando processamento da Transaction {transaction._id}!")
        #lock
        origem = self.bank.accounts[transaction.origin[1] - 1]
        destino = self.bank.accounts[transaction.destination[1] - 1]
 
        #se origem e destino sao do mesmo banco
        if (self.bank._id == transaction.destination[0]):  # se sao do mesmo banco é nacional
            status_withdraw = origem.withdraw(transaction.amount)

            cheque_especial_usado = origem.valor_especial_usado
            if (cheque_especial_usado > 0):
                transaction.amount -= cheque_especial_usado * 0.05
                self.bank.lock_bank_profit.acquire()
                self.bank.bank_profit += ((origem.valor_especial_usado * 0.05))
                self.bank.lock_bank_profit.release()
            origem.account_semaphore.release()  #é aqui que é feito o release da retirada
    
            if status_withdraw:
                #descontar = cheque_especial_usado * 0.05
                destino.deposit(transaction.amount)
                transaction.set_status(TransactionStatus.SUCCESSFUL)
                self.bank.lock_nacionais.acquire()
                self.bank.trans_nacionais += 1
                self.bank.lock_nacionais.release()
            else:
                transaction.set_status(TransactionStatus.FAILED)

        else: # internacional
            #transacao da conta origem p/ conta do banco
            #transaction.exchange_fee = self.bank.currency.get_exchange_rate(self.bank.currency.destino.currency) #retorna a taxa de conversao, talvez fazer um set na classe Transaction
            transaction.exchange_fee = get_exchange_rate(self.bank.currency, transaction.currency)
            
            tax = (transaction.exchange_fee * transaction.amount) * 0.01 #aplica a taxa de transferencia de 1%
            transfer_amount = (transaction.exchange_fee * transaction.amount) + tax #valor que vai ser transferido para conta destino

            self.bank.lock_bank_profit.acquire()
            self.bank.bank_profit += tax
            self.bank.lock_bank_profit.release()

            if destino._bank_id == 1:
                self.bank.reserves.USD.deposit(transfer_amount)  #primeiro deposita na conta interna
                deposit = self.bank.reserves.USD.withdraw(transfer_amount)
                self.bank.reserves.USD.account_semaphore.release() 

            elif destino._bank_id == 2:
                self.bank.reserves.EUR.deposit(transfer_amount)
                deposit = self.bank.reserves.EUR.withdraw(transfer_amount)
                self.bank.reserves.EUR.account_semaphore.release() 

            elif destino._bank_id == 3:
                self.bank.reserves.GBP.deposit(transfer_amount)
                deposit = self.bank.reserves.GBP.withdraw(transfer_amount)
                self.bank.reserves.GBP.account_semaphore.release() 

            elif destino._bank_id == 4:
                self.bank.reserves.JPY.deposit(transfer_amount)
                deposit = self.bank.reserves.JPY.withdraw(transfer_amount)
                self.bank.reserves.JPY.account_semaphore.release() 

            elif destino._bank_id == 5:
                self.bank.reserves.CHF.deposit(transfer_amount)
                deposit = self.bank.reserves.CHF.withdraw(transfer_amount)
                self.bank.reserves.CHF.account_semaphore.release() 

            else:
                self.bank.reserves.BRL.deposit(transfer_amount)
                deposit = self.bank.reserves.BRL.withdraw(transfer_amount)
                self.bank.reserves.BRL.account_semaphore.release() 
            
            cheque_especial_usado = origem.valor_especial_usado
            if (cheque_especial_usado > 0):
                transfer_amount -= cheque_especial_usado * 0.05
                self.bank.lock_bank_profit.acquire()
                self.bank.bank_profit += ((origem.valor_especial_usado * 0.05) + tax)
                self.bank.lock_bank_profit.release()

            if deposit:
                if destino.deposit(transfer_amount):
                    transaction.set_status(TransactionStatus.SUCCESSFUL)
                    self.bank.lock_inter.acquire()
                    self.bank.trans_inter += 1
                    self.bank.lock_inter.release()
                else:
                    transaction.set_status(TransactionStatus.FAILED)
           
        if (transaction.status == TransactionStatus.FAILED):
            self.bank.lock_transfers.acquire()
            self.bank.total_transfers += 1
            self.bank.time_transfers += transaction.get_processing_time().total_seconds()
            self.bank.lock_transfers.release()

        # NÃO REMOVA ESSE SLEEP!
        # Ele simula uma latência de processamento para a transação.
        time.sleep(3 * time_unit)

        #transaction.set_status(TransactionStatus.SUCCESSFUL)
        return transaction.status

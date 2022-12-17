from typing import Tuple

from payment_system.account import Account, CurrencyReserves
from utils.transaction import Transaction
from threading import Semaphore, Lock
from utils.currency import Currency
from utils.logger import LOGGER


class Bank():
    """
    Uma classe para representar um Banco.
    Se você adicionar novos atributos ou métodos, lembre-se de atualizar essa docstring.

    ...

    Atributos
    ---------
    _id : int
        Identificador do banco.
    currency : Currency
        Moeda corrente das contas bancárias do banco.
    reserves : CurrencyReserves
        Dataclass de contas bancárias contendo as reservas internas do banco.
    operating : bool
        Booleano que indica se o banco está em funcionamento ou não.
    accounts : List[Account]
        Lista contendo as contas bancárias dos clientes do banco.
    transaction_queue : Queue[Transaction]
        Fila FIFO contendo as transações bancárias pendentes que ainda serão processadas.
    lock_transaction : Lock()
        Lock utilizado para para proteger a região critica onde é retirada uma transação da fila
    sem_queue : Semaphore()
        Semafaro pra bloquear outras threads
    processors_list : List
        Lista dos processos
    lock_nacionais: Lock()
        Lock utilizado para protegem o incremento de trans_nacionais
    trans_nacionais: int
        numero de transaçoes nacionais
    lock_inter :Lock()
        Lock utilizado para protegem o incremento de trans_nacionais
    trans_inter: int
        numero de transaçoes internacionais
    lock_bank_profit: Lock()
        Lock utilizado para protegem o incremento do lucro do banco(self.bank_profit)
    bank_profit : int
        Lucro do banco
    lock_transfers: Lock()
        Lock utilizado nas transferencias
    time_transfers: int
        Tempo total em que as transações ficaram na fila de espera
    total_transfers: int
        numero de transacoes processadas
    saldo: int
        saldo total de todas as contas bancarias do banco

    Métodos
    -------
    new_account(balance: int = 0, overdraft_limit: int = 0) -> None:
        Cria uma nova conta bancária (Account) no banco.
    new_transfer(origin: Tuple[int, int], destination: Tuple[int, int], amount: int, currency: Currency) -> None:
        Cria uma nova transação bancária.
    info() -> None:
        Printa informações e estatísticas sobre o funcionamento do banco.
    
    """

    def __init__(self, _id: int, currency: Currency):
        self._id                = _id
        self.currency           = currency
        self.reserves           = CurrencyReserves()
        self.operating          = False
        self.accounts           = []
        self.transaction_queue  = []
        self.lock_transaction   = Lock()
        self.sem_queue          = Semaphore(0)
        self.processors_list    = []
        self.generator          = None

        self.lock_nacionais     = Lock()
        self.trans_nacionais    = 0     #num de trans nacionais

        self.lock_inter         = Lock()
        self.trans_inter        = 0 

        self.lock_bank_profit   = Lock()
        self.bank_profit        = 0     #lucro do banco

        self.lock_transfers     = Lock()
        self.time_transfers     = 0     #tempo total em que as transferencias ficaram na fila
        self.total_transfers    = 0

        self.lock_saldo         = Lock()
        self.saldo              = 0     #saldo total de todas as contas bancarias


    def new_account(self, balance: int = 0, overdraft_limit: int = 0) -> None:
        """
        Esse método deverá criar uma nova conta bancária (Account) no banco com determinado 
        saldo (balance) e limite de cheque especial (overdraft_limit).
        """
        # TODO: IMPLEMENTE AS MODIFICAÇÕES, SE NECESSÁRIAS, NESTE MÉTODO!

        # Gera _id para a nova Account
        acc_id = len(self.accounts) + 1

        # Cria instância da classe Account
        acc = Account(_id=acc_id, _bank_id=self._id, currency=self.currency, balance=balance, overdraft_limit=overdraft_limit)
  
        # Adiciona a Account criada na lista de contas do banco
        self.accounts.append(acc)


    def info(self) -> None:
        """
        Essa função deverá printar os seguintes dados utilizando o LOGGER fornecido:
        1. Saldo de cada moeda nas reservas internas do banco
        2. Número de transferências nacionais e internacionais realizadas
        3. Número de contas bancárias registradas no banco
        4. Saldo total de todas as contas bancárias (dos clientes) registradas no banco
        5. Lucro do banco: taxas de câmbio acumuladas + juros de cheque especial acumulados
        """
        # TODO: IMPLEMENTE AS MODIFICAÇÕES, SE NECESSÁRIAS, NESTE MÉTODO!

        LOGGER.info(f"-----------------------------------------------------------------------------------")
        LOGGER.info(f"Estatísticas do Banco Nacional {self._id}:\n")

        LOGGER.info(f"1. Saldo de cada moeda nas reservas internas do banco")
        LOGGER.info(f"BRL = {self.reserves.BRL.balance}")
        LOGGER.info(f"CHF = {self.reserves.CHF.balance}")
        LOGGER.info(f"EUR = {self.reserves.EUR.balance}")
        LOGGER.info(f"GBP = {self.reserves.GBP.balance}")
        LOGGER.info(f"JPY = {self.reserves.JPY.balance}")
        LOGGER.info(f"USD = {self.reserves.USD.balance}\n")

        LOGGER.info(f"2. Número de transferências nacionais e internacionais realizadas")
        LOGGER.info(f"Nacionais = {self.trans_nacionais}")
        LOGGER.info(f"Internacionais = {self.trans_inter}\n")

        LOGGER.info(f"3. Número de contas bancárias registradas no banco")
        LOGGER.info(f"Total = {len(self.accounts)}\n")

        LOGGER.info(f"4. Saldo total de todas as contas bancárias (dos clientes) registradas no banco")
        self.lock_saldo.acquire()
        for account in self.accounts:
            self.saldo += account.balance
        self.lock_saldo.release()
        LOGGER.info(f"Saldo das contas = {self.saldo}\n")

        LOGGER.info(f"5. Lucro do banco: taxas de câmbio acumuladas + juros de cheque especial acumulados")
        LOGGER.info(f"Lucro do Banco = {self.bank_profit}\n")

        LOGGER.info(f"6. Quantidade total de transações que não foram processadas")
        LOGGER.info(f"Pendentes = {len(self.transaction_queue)}")
        LOGGER.info(f"Falhas = {self.total_transfers}\n")

        LOGGER.info(f"7. Média de tempo em que as transações ficaram nas filas de espera")
        LOGGER.info(f"Total = {self.time_transfers}")
        LOGGER.info(f"Média = {self.time_transfers/(len(self.transaction_queue)+self.total_transfers)}\n")




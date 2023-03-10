import argparse, time, sys
from logging import INFO, DEBUG
from random import randint

from globals import *
from payment_system.bank import Bank
from payment_system.payment_processor import PaymentProcessor
from payment_system.transaction_generator import TransactionGenerator
from utils.currency import Currency
from utils.logger import CH, LOGGER


if __name__ == "__main__":
    # Verificação de compatibilidade da versão do python:
    if sys.version_info < (3, 5):
        sys.stdout.write('Utilize o Python 3.5 ou mais recente para desenvolver este trabalho.\n')
        sys.exit(1)

    # Captura de argumentos da linha de comando:
    parser = argparse.ArgumentParser()
    parser.add_argument("--time_unit", "-u", help="Valor da unidade de tempo de simulação")
    parser.add_argument("--total_time", "-t", help="Tempo total de simulação")
    parser.add_argument("--debug", "-d", help="Printar logs em nível DEBUG")
    args = parser.parse_args()
    if args.time_unit:
        time_unit = float(args.time_unit)
    if args.total_time:
        total_time = int(args.total_time)
    if args.debug:
        debug = True

    # Configura logger
    if debug:
        LOGGER.setLevel(DEBUG)
        CH.setLevel(DEBUG)
    else:
        LOGGER.setLevel(INFO)
        CH.setLevel(INFO)

    # Printa argumentos capturados da simulação
    LOGGER.info(f"Iniciando simulação com os seguintes parâmetros:\n\ttotal_time = {total_time}\n\tdebug = {debug}\n")
    time.sleep(3)

    # Inicializa variável `tempo`:
    t = 0
    
    # Cria os Bancos Nacionais e popula a lista global `banks`:
    for i, currency in enumerate(Currency):
        
        # Cria Banco Nacional
        bank = Bank(_id=i, currency=currency)
        
        # Deposita valores aleatórios nas contas internas (reserves) do banco
        bank.reserves.BRL.deposit(randint(100_000_000, 10_000_000_000))
        bank.reserves.CHF.deposit(randint(100_000_000, 10_000_000_000))
        bank.reserves.EUR.deposit(randint(100_000_000, 10_000_000_000))
        bank.reserves.GBP.deposit(randint(100_000_000, 10_000_000_000))
        bank.reserves.JPY.deposit(randint(100_000_000, 10_000_000_000))
        bank.reserves.USD.deposit(randint(100_000_000, 10_000_000_000))
        
        # Adiciona banco na lista global de bancos
        banks.append(bank)
        bank.operating = True

    for bank in banks:
        for i in range(100):
            bank.new_account(randint(0, 100000), randint(0, 100000))


    generators = []
    processors =  []
    # Inicializa gerador de transações e processadores de pagamentos para os Bancos Nacionais:
    for i, bank in enumerate(banks):
        # Inicializa um TransactionGenerator thread por banco:
        generator = TransactionGenerator(_id=i, bank=bank)
        generators.append(generator)
        generator.start()
        # Inicializa um PaymentProcessor thread por banco.
        # Sua solução completa deverá funcionar corretamente com múltiplos PaymentProcessor threads para cada banco.
        
        #PaymentProcessor(_id=i, bank=bank).start()
        for j in range(10):
            processor = PaymentProcessor(_id=i, bank=bank)
            processors.append(processor)
            processor.start()
        
    # Enquanto o tempo total de simuação não for atingido:
    while t < total_time:
        # Aguarda um tempo aleatório antes de criar o próximo cliente:
        dt = randint(0, 3)
        time.sleep(dt * time_unit)

        # Atualiza a variável tempo considerando o intervalo de criação dos clientes:
        t += dt

    # Finaliza todas as threads
    for bank in banks:
        bank.operating = False

    for g in generators:
        g.join()

    for bank in banks:
        bank.sem_queue.release()

    for p in processors:
        p.join()

    # Termina simulação. Após esse print somente dados devem ser printados no console.
    LOGGER.info(f"A simulação chegou ao fim!\n")
    
    for bank in banks:
        bank.info()

    total_time  = 0
    total_fails = 0

    for bank in banks:
        total_time += bank.time_transfers
        total_fails += (bank.total_transfers + len(bank.transaction_queue))

    LOGGER.info(f"-----------------------------------------------------------------------------------")
    LOGGER.info(f"Estatísticas Gerais:\n")
    LOGGER.info(f"Quantidade total (de todos os bancos) de transacões que NÃO foram processadas")
    LOGGER.info(f"Total = {total_fails}\n")
    
    LOGGER.info(f"Média de tempo em que elas ficaram nas filas de espera.")
    LOGGER.info(f"Média = {total_time/total_fails}\n")

# class definition that uses inheritance — it's subclassing the built-in Exception class 
# To create a custom exception (also called a user-defined exception).

class InsufficientFundsError(Exception):
    """Raised when a withdrawal exceeds the available balance."""
    pass

class BankAccount:
    bank_name = "Bank of America"   # class variable, shared by all accounts
    total_accounts = 0              # tracks how many accounts exist

    def __init__(self, name: str, account_num: str, balance: float = 0.0): # constructor
        self.name = name
        self.account_num = account_num
        self.balance = balance
        BankAccount.total_accounts += 1   
        # increment on every new account - Class variable
        # class attribute access — we are looking it up on the class, not on self.
# object methods
    def deposit(self, amt: float):
        if amt <= 0:
            raise ValueError("Deposit amount must be positive")
        self.balance += amt

    def withdraw(self, amt: float):
        self._validate_withdrawal(amt)
        self.balance -= amt

    def check_balance(self) -> float:
        return self.balance

    def display_account_details(self):
        print("Account Name:", self.name)
        print("Account Number:", self.account_num)
        print("Balance:", self.balance)
        print("Bank Name:", self.bank_name)


    @classmethod
    def set_bank_name(cls, new_name: str):
        cls.bank_name = new_name

    @classmethod
    def get_total_accounts(cls) -> int:
        return cls.total_accounts

    def _validate_withdrawal(self, amt: float): # Private procedure
        if amt > self.balance:
            raise InsufficientFundsError(f"Cannot withdraw {amt}, balance is {self.balance}")





# --- quick test ---
a1 = BankAccount("Alice", "ACC001", 1000)
a2 = BankAccount("Bob", "ACC002", 500)

a1.deposit(200)
print("-----------------")
a1.display_account_details()
print("-----------------")

try:
    a2.withdraw(60000)
except InsufficientFundsError as e:
    print("Error:", e)

BankAccount.set_bank_name("Chase")
print(a1.bank_name, 
      a2.bank_name)   # both object change — it's shared

print("Total accounts:", BankAccount.get_total_accounts())



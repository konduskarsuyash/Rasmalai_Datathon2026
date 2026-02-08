// utils/localSimulationEngine.js

/**
 * Local Simulation Engine
 * Runs simulation step-by-step in the frontend with pause/resume/modify capabilities
 */

export class LocalSimulationEngine {
  constructor(initialBanks, initialConnections, config = {}) {
    // Configuration
    this.config = {
      interestRate: config.interestRate || 0.05, // 5% interest per step
      loanRepaymentRate: config.loanRepaymentRate || 0.1, // 10% repayment per step
      marketVolatility: config.marketVolatility || 0.02, // 2% price change
      defaultThreshold: config.defaultThreshold || 0, // Default if capital <= 0
      ...config
    };
    
    console.log('🚀 LocalSimulationEngine initializing...');
    console.log('Initial banks:', initialBanks);
    console.log('Initial connections:', initialConnections);
    
    // State
    this.banks = this.initializeBanks(initialBanks);
    this.loans = this.initializeLoans(initialConnections);
    this.markets = this.initializeMarkets(initialBanks);
    
    console.log('✅ Initialized banks:', this.banks);
    console.log('✅ Initialized loans:', this.loans);
    console.log('✅ Initialized markets:', this.markets);
    
    // Simulation state
    this.currentStep = 0;
    this.isRunning = false;
    this.isPaused = false;
    this.history = [];
    this.transactionLog = [];
    
    // Callbacks
    this.onStepComplete = null;
    this.onTransaction = null;
    this.onBankDefault = null;
    this.onStateChange = null;
  }
  
  initializeBanks(initialBanks) {
    return initialBanks
      .filter(b => b.type === 'bank' && !b.isMarket)
      .map((bank, index) => ({
        id: index,
        name: bank.name,
        capital: bank.capital || 100,
        cash: (bank.capital || 100) * 0.5, // 50% as cash (increased from 30%)
        investments: {},
        loansGiven: {}, // { bankId: amount }
        loansTaken: {}, // { bankId: amount }
        targetLeverage: bank.target || 3.0,
        riskFactor: bank.risk || 0.2,
        isDefaulted: false,
        history: []
      }));
  }

  initializeMarkets(initialInstitutions) {
    const marketNodes = initialInstitutions.filter(b => b.type === 'market' || b.isMarket);
    const markets = {};
    for (const m of marketNodes) {
      markets[m.id] = { price: 100, totalInvested: 0, history: [100] };
    }
    console.log(`📊 Initialized ${Object.keys(markets).length} markets from institutions`);
    return markets;
  }
  
  initializeLoans(connections) {
    return connections
      .filter(c => c.type === 'credit' || c.type === 'lending')
      .map(conn => ({
        id: conn.id,
        from: parseInt(conn.source.replace('bank', '')) - 1,
        to: parseInt(conn.target.replace('bank', '')) - 1,
        principal: conn.exposure || 0,
        interestAccrued: 0,
        stepsActive: 0
      }));
  }
  
  // Start simulation
  start() {
    console.log('🎬 Starting simulation with', this.banks.length, 'banks');
    this.isRunning = true;
    this.isPaused = false;
    this.runLoop();
  }
  
  // Pause simulation
  pause() {
    this.isPaused = true;
    this.notifyStateChange();
  }
  
  // Resume simulation
  resume() {
    this.isPaused = false;
    this.runLoop();
  }
  
  // Stop simulation
  stop() {
    this.isRunning = false;
    this.isPaused = false;
    this.notifyStateChange();
  }
  
  // Main simulation loop
  async runLoop() {
    while (this.isRunning && !this.isPaused) {
      await this.step();
      await this.sleep(1000); // 1 second per step
    }
  }
  
  // Execute one simulation step
  async step() {
    this.currentStep++;
    console.log(`\n📍 Step ${this.currentStep} starting...`);
    
    // 1. Apply interest to all loans
    this.applyInterest();
    
    // 2. Process loan repayments
    this.processRepayments();
    
    // 3. Each bank makes decisions
    for (const bank of this.banks) {
      if (bank.isDefaulted) continue;
      await this.executeBankAction(bank);
    }
    
    // 4. Update market prices
    this.updateMarkets();
    
    // 5. Check for defaults
    this.checkDefaults();
    
    // 6. Record history
    this.recordHistory();
    
    console.log(`✅ Step ${this.currentStep} complete. Transactions this step:`, this.transactionLog.filter(t => t.step === this.currentStep).length);
    
    // 7. Notify step complete
    if (this.onStepComplete) {
      this.onStepComplete(this.getState());
    }
    
    this.notifyStateChange();
  }
  
  // Apply interest to all active loans
  applyInterest() {
    for (const loan of this.loans) {
      const interest = loan.principal * this.config.interestRate;
      loan.interestAccrued += interest;
      loan.stepsActive++;
      
      // Deduct interest from borrower
      const borrower = this.banks[loan.to];
      if (borrower && !borrower.isDefaulted) {
        borrower.capital -= interest;
        borrower.cash -= interest;
      }
      
      // Add interest to lender
      const lender = this.banks[loan.from];
      if (lender && !lender.isDefaulted) {
        lender.capital += interest;
        lender.cash += interest;
      }
      
      this.logTransaction({
        type: 'INTEREST_PAYMENT',
        from: loan.to,
        to: loan.from,
        amount: interest,
        step: this.currentStep
      });
    }
  }
  
  // Process automatic loan repayments
  processRepayments() {
    for (const loan of this.loans) {
      const borrower = this.banks[loan.to];
      if (!borrower || borrower.isDefaulted) continue;
      
      // Try to repay 10% of principal + interest
      const repaymentAmount = Math.min(
        loan.principal * this.config.loanRepaymentRate,
        borrower.cash * 0.5 // Don't use more than 50% of cash
      );
      
      if (repaymentAmount > 0) {
        loan.principal -= repaymentAmount;
        borrower.cash -= repaymentAmount;
        borrower.capital -= repaymentAmount;
        
        const lender = this.banks[loan.from];
        if (lender && !lender.isDefaulted) {
          lender.cash += repaymentAmount;
          lender.capital += repaymentAmount;
        }
        
        this.logTransaction({
          type: 'LOAN_REPAYMENT',
          from: loan.to,
          to: loan.from,
          amount: repaymentAmount,
          step: this.currentStep
        });
      }
    }
    
    // Remove fully repaid loans
    this.loans = this.loans.filter(loan => loan.principal > 0.1);
  }
  
  // Bank decision-making
  async executeBankAction(bank) {
    // Simple strategy based on risk factor
    const action = this.decideBankAction(bank);
    
    switch (action.type) {
      case 'LEND':
        this.executeLending(bank, action.target, action.amount);
        break;
      case 'INVEST':
        this.executeInvestment(bank, action.market, action.amount);
        break;
      case 'DIVEST':
        this.executeDivestment(bank, action.market, action.amount);
        break;
      case 'HOLD':
        // Log hold action for visibility
        this.logTransaction({
          type: 'HOARD_CASH',
          from: bank.id,
          to: null,
          market_id: null,
          amount: bank.cash,
          step: this.currentStep
        });
        break;
    }
    
    await this.sleep(300); // 300ms between actions
  }
  
  decideBankAction(bank) {
    const totalAssets = bank.cash + Object.values(bank.investments).reduce((a,b) => a+b, 0);
    const leverage = bank.capital > 0 ? totalAssets / bank.capital : 0;
    const cashRatio = bank.capital > 0 ? bank.cash / bank.capital : 0;
    const marketIds = Object.keys(this.markets);
    const hasMarkets = marketIds.length > 0;
    
    console.log(`Bank ${bank.id} deciding:`, { 
      capital: bank.capital.toFixed(1), 
      cash: bank.cash.toFixed(1), 
      cashRatio: cashRatio.toFixed(2),
      riskFactor: bank.riskFactor,
      marketsAvailable: marketIds.length
    });
    
    // Ensure bank has minimum cash to act
    if (bank.cash < 5) {
      console.log(`Bank ${bank.id} holding - insufficient cash`);
      return { type: 'HOLD' };
    }
    
    // High risk banks (>0.5) invest aggressively (only if markets exist)
    if (hasMarkets && bank.riskFactor > 0.5 && bank.cash > 10) {
      const market = marketIds[Math.floor(Math.random() * marketIds.length)];
      const amount = Math.min(bank.cash * 0.3, bank.cash - 5); // Keep $5 reserve
      console.log(`Bank ${bank.id} investing $${amount.toFixed(1)}M in ${market}`);
      return {
        type: 'INVEST',
        market: market,
        amount: amount
      };
    }
    
    // Medium risk banks (0.2-0.5) lend
    if (bank.riskFactor >= 0.2 && bank.riskFactor <= 0.5 && bank.cash > 15) {
      const target = this.findLoanTarget(bank);
      if (target !== null) {
        const amount = Math.min(bank.cash * 0.25, bank.cash - 10); // Keep $10 reserve
        console.log(`Bank ${bank.id} lending $${amount.toFixed(1)}M to Bank ${target}`);
        return {
          type: 'LEND',
          target: target,
          amount: amount
        };
      }
    }
    
    // High risk banks with no markets available — lend instead
    if (!hasMarkets && bank.riskFactor > 0.5 && bank.cash > 10) {
      const target = this.findLoanTarget(bank);
      if (target !== null) {
        const amount = Math.min(bank.cash * 0.3, bank.cash - 5);
        console.log(`Bank ${bank.id} (high risk, no markets) lending $${amount.toFixed(1)}M to Bank ${target}`);
        return {
          type: 'LEND',
          target: target,
          amount: amount
        };
      }
    }
    
    // Low risk banks (<0.2) are conservative but still lend small amounts
    if (bank.riskFactor < 0.2 && bank.cash > 20) {
      const target = this.findLoanTarget(bank);
      if (target !== null) {
        const amount = Math.min(bank.cash * 0.1, bank.cash - 15); // Keep $15 reserve
        console.log(`Bank ${bank.id} (conservative) lending $${amount.toFixed(1)}M to Bank ${target}`);
        return {
          type: 'LEND',
          target: target,
          amount: amount
        };
      }
    }
    
    // If cash is very high (>50% of capital) and markets exist, invest some
    if (hasMarkets && cashRatio > 0.5 && bank.cash > 20) {
      const market = marketIds[Math.floor(Math.random() * marketIds.length)];
      const amount = Math.min(bank.cash * 0.15, bank.cash - 15);
      console.log(`Bank ${bank.id} has excess cash, investing $${amount.toFixed(1)}M in ${market}`);
      return {
        type: 'INVEST',
        market: market,
        amount: amount
      };
    }
    
    // Default: hold cash
    console.log(`Bank ${bank.id} holding cash`);
    return { type: 'HOLD' };
  }
  
  findLoanTarget(bank) {
    const potentialBorrowers = this.banks.filter(b => 
      b.id !== bank.id && !b.isDefaulted && b.capital > 50
    );
    if (potentialBorrowers.length === 0) return null;
    return potentialBorrowers[Math.floor(Math.random() * potentialBorrowers.length)].id;
  }
  
  executeLending(lender, borrowerId, amount) {
    if (amount <= 0 || lender.cash < amount) return;
    
    const borrower = this.banks[borrowerId];
    if (!borrower || borrower.isDefaulted) return;
    
    // Transfer funds
    lender.cash -= amount;
    borrower.cash += amount;
    borrower.capital += amount;
    
    // Create loan
    this.loans.push({
      id: `loan-${this.currentStep}-${lender.id}-${borrowerId}`,
      from: lender.id,
      to: borrowerId,
      principal: amount,
      interestAccrued: 0,
      stepsActive: 0
    });
    
    // Update tracking
    lender.loansGiven[borrowerId] = (lender.loansGiven[borrowerId] || 0) + amount;
    borrower.loansTaken[lender.id] = (borrower.loansTaken[lender.id] || 0) + amount;
    
    this.logTransaction({
      type: 'INCREASE_LENDING',
      from: lender.id,
      to: borrowerId,
      amount: amount,
      step: this.currentStep
    });
  }
  
  executeInvestment(bank, marketId, amount) {
    if (amount <= 0 || bank.cash < amount) return;
    
    bank.cash -= amount;
    bank.investments[marketId] = (bank.investments[marketId] || 0) + amount;
    
    const market = this.markets[marketId];
    market.totalInvested += amount;
    
    this.logTransaction({
      type: 'INVEST_MARKET',
      from: bank.id,
      to: null,
      market_id: marketId,
      amount: amount,
      step: this.currentStep
    });
  }
  
  executeDivestment(bank, marketId, amount) {
    const invested = bank.investments[marketId] || 0;
    const actualAmount = Math.min(amount, invested);
    if (actualAmount <= 0) return;
    
    bank.investments[marketId] -= actualAmount;
    bank.cash += actualAmount;
    
    const market = this.markets[marketId];
    market.totalInvested -= actualAmount;
    
    this.logTransaction({
      type: 'DIVEST_MARKET',
      from: bank.id,
      to: null,
      market_id: marketId,
      amount: actualAmount,
      step: this.currentStep
    });
  }
  
  updateMarkets() {
    for (const [marketId, market] of Object.entries(this.markets)) {
      // Price changes based on net flow
      const priceChange = (Math.random() - 0.5) * this.config.marketVolatility * 100;
      market.price = Math.max(50, market.price + priceChange);
      market.history.push(market.price);
    }
  }
  
  checkDefaults() {
    for (const bank of this.banks) {
      if (!bank.isDefaulted && bank.capital <= this.config.defaultThreshold) {
        bank.isDefaulted = true;
        if (this.onBankDefault) {
          this.onBankDefault(bank);
        }
      }
    }
  }
  
  recordHistory() {
    const snapshot = {
      step: this.currentStep,
      banks: this.banks.map(b => ({
        id: b.id,
        name: b.name,
        capital: b.capital,
        cash: b.cash,
        totalInvestments: Object.values(b.investments).reduce((a,b) => a+b, 0),
        totalLoansGiven: Object.values(b.loansGiven).reduce((a,b) => a+b, 0),
        totalLoansTaken: Object.values(b.loansTaken).reduce((a,b) => a+b, 0),
        isDefaulted: b.isDefaulted
      })),
      markets: Object.entries(this.markets).map(([id, m]) => ({
        id,
        price: m.price,
        totalInvested: m.totalInvested
      }))
    };
    
    this.history.push(snapshot);
  }
  
  logTransaction(tx) {
    this.transactionLog.push(tx);
    if (this.onTransaction) {
      this.onTransaction(tx);
    }
  }
  
  // Modification methods (during pause)
  addCapitalToBank(bankId, amount) {
    const bank = this.banks.find(b => b.id === bankId);
    if (bank) {
      bank.capital += amount;
      bank.cash += amount;
      this.notifyStateChange();
    }
  }
  
  removeBank(bankId) {
    // Remove bank and all its loans
    this.banks = this.banks.filter(b => b.id !== bankId);
    this.loans = this.loans.filter(l => l.from !== bankId && l.to !== bankId);
    this.notifyStateChange();
  }
  
  addBank(bankConfig) {
    const newId = Math.max(...this.banks.map(b => b.id), -1) + 1;
    this.banks.push({
      id: newId,
      name: bankConfig.name || `Bank ${newId}`,
      capital: bankConfig.capital || 100,
      cash: (bankConfig.capital || 100) * 0.3,
      investments: {},
      loansGiven: {},
      loansTaken: {},
      targetLeverage: bankConfig.target || 3.0,
      riskFactor: bankConfig.risk || 0.2,
      isDefaulted: false,
      history: []
    });
    this.notifyStateChange();
  }
  
  // Getters
  getState() {
    return {
      step: this.currentStep,
      isRunning: this.isRunning,
      isPaused: this.isPaused,
      banks: this.banks,
      loans: this.loans,
      markets: this.markets,
      history: this.history,
      transactions: this.transactionLog
    };
  }
  
  // Helpers
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
  
  notifyStateChange() {
    if (this.onStateChange) {
      this.onStateChange(this.getState());
    }
  }
}

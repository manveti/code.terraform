counts = {}
for num in range(1, 6):
    result = self.contract.terminal.guess([num] * self.contract.terminal.length)
    counts[num] = result.correct
slots = list(range(self.contract.terminal.length))
guess = [1] * self.contract.terminal.length
correct = counts[1]
guessNum = 2
guessPlaced = 0
while correct < self.contract.terminal.length:
    while guessPlaced >= counts[guessNum]:
        guessPlaced = 0
        guessNum += 1
        if guessNum > 5:
            break
    if guessNum > 5:
        break
    for i in range(len(slots)):
        newGuess = guess[:]
        newGuess[slots[i]] = guessNum
        result = self.contract.terminal.guess(newGuess)
        if result.misplaced == 0:
            guess = newGuess
            guessPlaced += 1
            del slots[i]
            break
transmitter = get_component("transmitter")
transmitter.connect("earth")
transmitter.transmit(self.contract.id, guess)
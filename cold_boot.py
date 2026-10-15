OUTPUT_OFFSET = ord('A') - 1

def getParams(memory, addr, modes, n):
    params = []
    for i in range(n):
        modes = floor(modes / 10)
        mode = modes % 10
        addr += 1
        param = memory[addr]
        if not mode:
            param = memory[param]
        params.append(param)
    return params

def executeProgram(program):
    memory = list(program)
    output = []
    pc = 0
    while pc < len(memory):
        instruction = memory[pc]
        opcode = instruction % 100
        if opcode == 99:
            break
        if opcode == 1:
            params = getParams(memory, pc, floor(instruction / 10), 2)
            dest = memory[pc + 3]
            memory[dest] = params[0] + params[1]
            pc += 4
        elif opcode == 2:
            params = getParams(memory, pc, floor(instruction / 10), 2)
            dest = memory[pc + 3]
            memory[dest] = params[0] * params[1]
            pc += 4
        elif opcode == 4:
            params = getParams(memory, pc, floor(instruction / 10), 1)
            output.append(chr(params[0] + OUTPUT_OFFSET))
            pc += 2
        elif opcode == 5:
            params = getParams(memory, pc, floor(instruction / 10), 2)
            if params[0]:
                pc = params[1]
            else:
                pc += 3
        else:
            warn(f"Unrecognized opcode: {opcode}")
            return
    return output

output = executeProgram(self.contract.program)
msg = "".join(output)
print(msg)
transmitter = get_component("transmitter")
transmitter.connect("earth")
transmitter.transmit(self.contract.id, msg)
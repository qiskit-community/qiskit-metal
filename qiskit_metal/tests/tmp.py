class A():

    def __init__(self):
        self.made = False


class B(A):

    def __init__(self):
        super().__init__()
        self._b = "b"
        self.B = "B"


class C(B):

    def __init__(self):
        super().__init__()
        self._c = "cooL"


myc = C()
print(myc._c)
print(myc.B)
print(myc._b)
print(myc.made)

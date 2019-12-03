class Tree:
    def __init__(self, content, left=None, right=None):
        self.content = content
        self.left = left
        self.right = right

    def inorder(self, root):
        res = []
        
        if root:
            res = self.inorder(root.left)
            res.append(root.content)
            res = res + self.inorder(root.right)

        return res
def test_logic():
    print("Testing BranchShift Logic...")
    
    import random
    code = f"TEST{random.randint(1000, 9999)}"
    
    # Create a dummy branch
    branch = Branch.objects.create(
        name=f"Test Branch {code}",
        code=code,
        working_days=['saturday', 'sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday']
    )
    print(f"Created Branch: {branch.name}")
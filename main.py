# Frederik JH de Haas

from mip import Model, xsum, minimize, INTEGER
from itertools import product


def main():
    # Parameters
    n_departments = 3
    n_months = 6
    target_hours = [
        [1900, 1700, 1600, 1900, 1500, 1800],
        [1900, 1700, 1600, 1900, 1500, 1800],
        [1900, 1700, 1600, 1900, 1500, 1800],
    ]
    cumulative_resignations = [
        [0, 0, 0, 3, 3, 3],
        [0, 0, 0, 0, 5, 5],
        [0, 0, 0, 0, 0, 6],
    ]
    employees_beginning = [25, 20, 18]
    trainees_beginning = [2, 2, 2]
    training_capacity_per_month = 6
    trainee_cost = 50000
    understaffing_cost = 60000
    trainee_contribution_hours = 35
    employee_contibution_hours = 100
    salary_employee = 10000
    m = Model()

    # Decision Variables
    X = range(n_departments * n_months)
    Y = range(n_departments * n_months)

    # The number of hires in department i in month j
    x = [
        [m.add_var(var_type=INTEGER) for j in range(n_months)]
        for i in range(n_departments)
    ]
    # The number of underemployed employees in department i in month j
    y = [
        [m.add_var(var_type=INTEGER) for j in range(n_months)]
        for i in range(n_departments)
    ]

    # cost of training a trainee plus the cost of understaffed employee plus the salary of a hire
    m.objective = minimize(
        xsum(
            trainee_cost * x[dep][month]  # trainee cost.
            + understaffing_cost * y[dep][month]  # understaffing cost.
            + salary_employee
            * (n_months - month)
            * x[dep][
                month
            ]  # personal touch: use salary as an incentive to hire employees as late as possible.
            for dep, month in product(range(n_departments), range(n_months))
        )
    )

    def hours_available_from_hires(dep, month):
        # number of hours available from the hires in department i at time j
        def get_hours(hiring_month, focal_month):
            return (
                employee_contibution_hours
                if focal_month >= hiring_month + 2
                else trainee_contribution_hours
            )

        return xsum(
            x[dep][month__] * get_hours(month__, month) for month__ in range(month + 1)
        )

    def hours_available_default(dep, month):
        # hours available from full time hires at beginning:
        full_time_hires_hours = employee_contibution_hours * employees_beginning[dep]

        # hours available from trainees at beginning:
        if month == 0:
            trainees_hours = trainee_contribution_hours * trainees_beginning[dep]
        else:
            trainees_hours = employee_contibution_hours * trainees_beginning[dep]

        # hours lost due to resignation
        resignation_hours = (
            employee_contibution_hours * cumulative_resignations[dep][month]
        )

        return full_time_hires_hours + trainees_hours - resignation_hours

    # Constraint 1: understaffing constraint
    # we should meet the target hours per department per month
    for dep, month in product(range(n_departments), range(n_months)):
        m += (
            hours_available_default(dep, month)
            + hours_available_from_hires(dep, month)
            + 100
            * y[dep][month]  # The rest can be compensated by underemployed workers
            >= target_hours[dep][month]
        )

    # Constraint 2: training capacity costraint
    # can only train certain number of emplopyees per month.
    for month in range(n_months):
        m += (
            xsum(x[i][month] for i in range(n_departments))
            <= training_capacity_per_month
        )

    # Constraint 3: bleeding employees constraint
    # all the resigned employees have to be at least replaced in the end by new employees
    m += xsum(
        x[dep][month]
        for dep, month in product(range(n_departments), range(n_months - 2))
    ) + sum(trainees_beginning) >= sum(
        max(cumulative_resignations[department]) for department in range(n_departments)
    )

    m.optimize()

    for department in range(n_departments):
        print(f"DEPARTMENT {department}")
        print(
            "month \t # of hired trainees \t # of underemployed \t # of hours available \t # of hours required"
        )
        for month in range(n_months):
            print(
                month,
                "\t",
                int(x[department][month].x),
                "\t\t\t",
                int(y[department][month].x),
                "\t\t\t",
                hours_available_default(department, month)
                + hours_available_from_hires(department, month).x,
                "\t\t",
                target_hours[department][month],
            )

        print("\n\n")


if __name__ == "__main__":
    main()
